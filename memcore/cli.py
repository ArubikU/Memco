#!/usr/bin/env python3
import os
import sys
import argparse
import json
import time
import csv
from typing import List, Dict, Any, Optional, Tuple, Union
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.syntax import Syntax
from rich import box
import signal
import datetime

# Import from our memory system
from memcore import (
    MemCore, MemoryBuilder, MemoryRecord, 
    create_mem_folder, add_memory, memql_query, 
    update_memory, export_json, import_json
)

# Initialize rich console
console = Console()

# Global variables
active_server = None

def signal_handler(sig, frame):
    """Handle Ctrl+C to gracefully exit the program."""
    if active_server:
        console.print("[yellow]Stopping server...[/yellow]")
        from .server import stop_server
        stop_server()
    console.print("[yellow]Exiting MemCore CLI...[/yellow]")
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)

def server_command(args):
    """Start the MemCore server."""
    global active_server
    
    try:
        from .server import start_server
        
        console.print(f"[cyan]Starting MemCore server on {args.host}:{args.port}...[/cyan]")
        
        # Start server
        active_server = start_server(
            host=args.host,
            port=args.port,
            mem_path=args.path,
            encryption_key=args.key
        )
        
        console.print(f"[green]Server started successfully![/green]")
        console.print(f"[green]API available at http://{args.host}:{args.port}[/green]")
        console.print("[yellow]Press Ctrl+C to stop the server.[/yellow]")
        
        # Keep the main thread running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("[yellow]Stopping server...[/yellow]")
            stop_server()
            console.print("[green]Server stopped.[/green]")
        
        return 0
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

def format_memory(memory: MemoryRecord) -> Panel:
    """Format a memory record for display."""
    content = f"[bold blue]ID:[/bold blue] {memory.id}\n"
    content += f"[bold blue]Content:[/bold blue] {memory.content}\n"
    
    # Format tags
    if isinstance(memory.tags, list):
        content += f"[bold blue]Tags:[/bold blue] {', '.join(memory.tags)}\n"
    else:
        content += f"[bold blue]Tags:[/bold blue] {memory.tags}\n"
    
    content += f"[bold blue]Importance:[/bold blue] {memory.importance}\n"
    content += f"[bold blue]Source:[/bold blue] {memory.source}\n"
    
    # Format timestamps
    created_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(memory.created_at)) if memory.created_at else "Unknown"
    updated_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(memory.updated_at)) if memory.updated_at else "Unknown"
    
    content += f"[bold blue]Created:[/bold blue] {created_time}\n"
    content += f"[bold blue]Updated:[/bold blue] {updated_time}\n"
    
    if memory.metadata:
        content += f"[bold blue]Metadata:[/bold blue] {json.dumps(memory.metadata, indent=2)}\n"
    
    if memory.embedding:
        content += f"[bold blue]Embedding:[/bold blue] Vector[{len(memory.embedding)} dimensions]\n"
    
    return Panel(content, title=f"Memory: {memory.id[:8]}...", border_style="blue")

def init_command(args):
    """Initialize a new memory folder."""
    path = args.path
    
    if os.path.exists(path):
        if not args.force:
            console.print(f"[red]Error: Path '{path}' already exists. Use --force to overwrite.[/red]")
            return 1
    
    try:
        success = create_mem_folder(path)
        
        if success:
            console.print(f"[green]Successfully initialized memory folder at '{path}'[/green]")
            return 0
        else:
            console.print(f"[red]Failed to initialize memory folder at '{path}'[/red]")
            return 1
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

def add_command(args):
    """Add a new memory."""
    try:
        # Initialize MemCore
        memcore = MemCore(
            root_path=args.path,
            encryption_key=args.key,
            embedding_provider=None  # We don't have embedding provider in this version
        )
        
        # Create memory builder
        builder = MemoryBuilder()
        
        # Set content
        if args.content:
            builder.set_content(args.content)
        elif args.file:
            try:
                with open(args.file, 'r') as f:
                    content = f.read()
                builder.set_content(content)
            except Exception as e:
                console.print(f"[red]Error reading file: {str(e)}[/red]")
                return 1
        else:
            # Interactive mode
            console.print("[yellow]Enter memory content (Ctrl+D to finish):[/yellow]")
            lines = []
            try:
                while True:
                    line = input()
                    lines.append(line)
            except EOFError:
                pass
            content = "\n".join(lines)
            builder.set_content(content)
        
        # Set tags
        if args.tags:
            builder.set_tags(args.tags)
        
        # Set importance
        if args.importance is not None:
            builder.set_importance(args.importance)
        
        # Set source
        if args.source:
            builder.set_source(args.source)
        
        # Build memory
        memory = builder.build()
        
        # Add to system
        memory_id = memcore.add_memory(memory, encrypted=args.encrypt)
        
        console.print(f"[green]Memory added successfully with ID: {memory_id}[/green]")
        console.print(format_memory(memcore.get_memory(memory_id)))
        
        return 0
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

def get_command(args):
    """Get a memory by ID."""
    try:
        # Initialize MemCore
        memcore = MemCore(
            root_path=args.path,
            encryption_key=args.key
        )
        
        # Get memory
        memory = memcore.get_memory(args.id)
        
        if not memory:
            console.print(f"[red]Memory with ID '{args.id}' not found.[/red]")
            return 1
        
        # Display memory
        console.print(format_memory(memory))
        
        return 0
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

def update_command(args):
    """Update a memory."""
    try:
        # Initialize MemCore
        memcore = MemCore(
            root_path=args.path,
            encryption_key=args.key
        )
        
        # Check if memory exists
        memory = memcore.get_memory(args.id)
        if not memory:
            console.print(f"[red]Memory with ID '{args.id}' not found.[/red]")
            return 1
        
        # Build update dictionary
        update_dict = {}
        
        if args.content:
            update_dict["content"] = args.content
        elif args.file:
            try:
                with open(args.file, 'r') as f:
                    update_dict["content"] = f.read()
            except Exception as e:
                console.print(f"[red]Error reading file: {str(e)}[/red]")
                return 1
        
        if args.tags:
            update_dict["tags"] = args.tags
        
        if args.importance is not None:
            update_dict["importance"] = args.importance
        
        if args.source:
            update_dict["source"] = args.source
        
        # Update memory
        success = memcore.update_memory(args.id, update_dict)
        
        if success:
            console.print(f"[green]Memory updated successfully.[/green]")
            console.print(format_memory(memcore.get_memory(args.id)))
            return 0
        else:
            console.print(f"[red]Failed to update memory.[/red]")
            return 1
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

def delete_command(args):
    """Delete a memory."""
    try:
        # Initialize MemCore
        memcore = MemCore(
            root_path=args.path,
            encryption_key=args.key
        )
        
        # Check if memory exists
        memory = memcore.get_memory(args.id)
        if not memory:
            console.print(f"[red]Memory with ID '{args.id}' not found.[/red]")
            return 1
        
        # Confirm deletion
        if not args.force:
            console.print(format_memory(memory))
            confirm = input("Are you sure you want to delete this memory? (y/N): ")
            if confirm.lower() != 'y':
                console.print("[yellow]Deletion cancelled.[/yellow]")
                return 0
        
        # Delete memory
        success = memcore.delete_memory(args.id)
        
        if success:
            console.print(f"[green]Memory deleted successfully.[/green]")
            return 0
        else:
            console.print(f"[red]Failed to delete memory.[/red]")
            return 1
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

def query_command(args):
    """Query memories using MemQL."""
    try:
        # Initialize MemCore
        memcore = MemCore(
            root_path=args.path,
            encryption_key=args.key
        )
        
        # Execute query
        with Progress(transient=True) as progress:
            task = progress.add_task("[cyan]Executing query...", total=1)
            memories = memcore.memql_query(args.query)
            progress.update(task, completed=1)
        
        # Display results
        if not memories:
            console.print("[yellow]No memories found matching the query.[/yellow]")
            return 0
        
        console.print(f"[green]Found {len(memories)} memories:[/green]")
        
        for i, memory in enumerate(memories):
            if args.full:
                console.print(format_memory(memory))
            else:
                # Simplified output
                content_preview = memory.content[:100] + ('...' if len(memory.content) > 100 else '')
                console.print(f"[bold]{i+1}.[/bold] [blue]{memory.id}[/blue]: {content_preview}")
                
                # Format tags
                if isinstance(memory.tags, list):
                    tags_str = ', '.join(memory.tags)
                else:
                    tags_str = str(memory.tags)
                similarity = ""
                
                console.print(f"   Tags: {tags_str}, Importance: {memory.importance}")
                console.print()
        
        return 0
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

def export_command(args):
    """Export memories to a JSON file."""
    try:
        # Initialize MemCore
        memcore = MemCore(
            root_path=args.path,
            encryption_key=args.key
        )
        
        # Export memories
        with Progress(transient=True) as progress:
            task = progress.add_task("[cyan]Exporting memories...", total=1)
            count = memcore.export_json(args.output)
            progress.update(task, completed=1)
        
        console.print(f"[green]Successfully exported {count} memories to '{args.output}'[/green]")
        return 0
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

def import_command(args):
    """Import memories from a JSON file."""
    try:
        # Initialize MemCore
        memcore = MemCore(
            root_path=args.path,
            encryption_key=args.key
        )
        
        # Import memories
        with Progress(transient=True) as progress:
            task = progress.add_task("[cyan]Importing memories...", total=1)
            count = memcore.import_json(args.input, args.encrypt)
            progress.update(task, completed=1)
        
        console.print(f"[green]Successfully imported {count} memories from '{args.input}'[/green]")
        return 0
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

def backup_command(args):
    """Create a backup of the memory system."""
    try:
        # Initialize MemCore
        memcore = MemCore(
            root_path=args.path,
            encryption_key=args.key
        )
        
        # Create backup
        with Progress(transient=True) as progress:
            task = progress.add_task("[cyan]Creating backup...", total=1)
            backup_path = memcore.backup()
            progress.update(task, completed=1)
        
        console.print(f"[green]Successfully created backup at '{backup_path}'[/green]")
        return 0
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

def restore_command(args):
    """Restore from a backup."""
    try:
        # Initialize MemCore
        memcore = MemCore(
            root_path=args.path,
            encryption_key=args.key
        )
        
        # Restore from backup
        with Progress(transient=True) as progress:
            task = progress.add_task("[cyan]Restoring from backup...", total=1)
            success = memcore.restore(args.backup)
            progress.update(task, completed=1)
        
        if success:
            console.print(f"[green]Successfully restored from backup at '{args.backup}'[/green]")
            return 0
        else:
            console.print(f"[red]Failed to restore from backup.[/red]")
            return 1
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

def list_command(args):
    """List all memories."""
    try:
        # Initialize MemCore
        memcore = MemCore(
            root_path=args.path,
            encryption_key=args.key
        )
        
        # Get all memories
        all_memories = []
        memory_ids = memcore.viewer.list_memories()
        
        for memory_id in memory_ids:
            memory = memcore.get_memory(memory_id)
            if memory:
                all_memories.append(memory)
        
        # Filter by tag if specified
        if args.tag:
            filtered_memories = []
            for memory in all_memories:
                if isinstance(memory.tags, list):
                    if any(args.tag.lower() in tag.lower() for tag in memory.tags):
                        filtered_memories.append(memory)
                elif isinstance(memory.tags, str):
                    if args.tag.lower() in memory.tags.lower():
                        filtered_memories.append(memory)
            all_memories = filtered_memories
        
        # Sort if specified
        if args.sort:
            if args.sort == "importance":
                all_memories.sort(key=lambda x: x.importance, reverse=args.desc)
            elif args.sort == "created":
                all_memories.sort(key=lambda x: x.created_at, reverse=args.desc)
            elif args.sort == "updated":
                all_memories.sort(key=lambda x: x.updated_at, reverse=args.desc)
        
        # Apply limit if specified
        if args.limit and args.limit > 0:
            all_memories = all_memories[:args.limit]
        
        if not all_memories:
            console.print("[yellow]No memories found.[/yellow]")
            return 0
        
        # Display results
        console.print(f"[green]Found {len(all_memories)} memories:[/green]")
        
        for i, memory in enumerate(all_memories):
            if args.full:
                console.print(format_memory(memory))
            else:
                # Simplified output
                content_preview = memory.content[:100] + ('...' if len(memory.content) > 100 else '')
                console.print(f"[bold]{i+1}.[/bold] [blue]{memory.id}[/blue]: {content_preview}")
                
                # Format tags
                if isinstance(memory.tags, list):
                    tags_str = ', '.join(memory.tags)
                else:
                    tags_str = str(memory.tags)
                
                console.print(f"   Tags: {tags_str}, Importance: {memory.importance}")
                console.print()
        
        return 0
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

def history_command(args):
    """Show the history of a memory."""
    try:
        # Initialize MemCore
        memcore = MemCore(
            root_path=args.path,
            encryption_key=args.key
        )
        
        # Get memory
        memory = memcore.get_memory(args.id)
        if not memory:
            console.print(f"[red]Memory with ID '{args.id}' not found.[/red]")
            return 1
        
        # Get history
        history = memcore.get_history(args.id)
        
        if not history:
            console.print("[yellow]No history found for this memory.[/yellow]")
            return 0
        
        # Display history
        console.print(f"[green]History for memory {args.id}:[/green]")
        
        for i, entry in enumerate(history):
            timestamp = entry["timestamp"]
            action = entry["action"]
            data = entry["data"]
            
            # Format timestamp
            formatted_time = f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]} {timestamp[8:10]}:{timestamp[10:12]}:{timestamp[12:14]}"
            
            console.print(f"[bold]{i+1}.[/bold] [blue]{formatted_time}[/blue]: [yellow]{action}[/yellow]")
            
            if args.full:
                # Show full data
                syntax = Syntax(json.dumps(data, indent=2), "json", theme="monokai")
                console.print(syntax)
            
            console.print()
        
        return 0
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

def stats_command(args):
    """Show statistics about the memory system."""
    try:
        # Initialize MemCore
        memcore = MemCore(
            root_path=args.path,
            encryption_key=args.key
        )
        
        # Get all memories
        all_memories = []
        memory_ids = memcore.viewer.list_memories()
        
        for memory_id in memory_ids:
            memory = memcore.get_memory(memory_id)
            if memory:
                all_memories.append(memory)
        
        # Calculate statistics
        total_memories = len(all_memories)
        
        # Count encrypted memories
        encrypted_memories = 0
        for memory_id in memory_ids:
            memory_data = memcore.table.get_memory(memory_id)
            if memory_data and memory_data.get("encrypted", False):
                encrypted_memories += 1
        
        # Count memories with embeddings
        embedded_memories = sum(1 for memory in all_memories if memory.embedding and len(memory.embedding) > 0)
        
        # Calculate average importance
        avg_importance = sum(memory.importance for memory in all_memories) / total_memories if total_memories > 0 else 0
        
        # Count tags
        tag_counts = {}
        for memory in all_memories:
            if isinstance(memory.tags, list):
                for tag in memory.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Sort tags by count
        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Create table
        table = Table(title="MemCore Statistics", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Memories", str(total_memories))
        table.add_row("Encrypted Memories", f"{encrypted_memories} ({encrypted_memories/total_memories*100:.1f}% of total)" if total_memories > 0 else "0")
        table.add_row("Memories with Embeddings", f"{embedded_memories} ({embedded_memories/total_memories*100:.1f}% of total)" if total_memories > 0 else "0")
        table.add_row("Average Importance", f"{avg_importance:.2f}")
        
        # Display table
        console.print(table)
        
        # Display top tags if available
        if top_tags:
            tags_table = Table(title="Top Tags", box=box.ROUNDED)
            tags_table.add_column("Tag", style="cyan")
            tags_table.add_column("Count", style="green")
            
            for tag, count in top_tags:
                tags_table.add_row(tag, str(count))
            
            console.print(tags_table)
        
        return 0
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

def batch_add_command(args):
    """Add multiple memories from a file."""
    try:
        # Initialize MemCore
        memcore = MemCore(
            root_path=args.path,
            encryption_key=args.key
        )
        
        # Determine file type
        file_path = args.file
        file_ext = os.path.splitext(file_path)[1].lower()
        
        memory_ids = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn()
        ) as progress:
            
            if file_ext == '.json':
                # Import from JSON
                task = progress.add_task("[cyan]Importing memories from JSON...", total=1)
                
                with open(file_path, 'r') as f:
                    memories_data = json.load(f)
                
                count = 0
                for memory_data in memories_data:
                    memory = MemoryRecord.from_dict(memory_data)
                    memory_id = memcore.add_memory(memory, encrypted=args.encrypt)
                    memory_ids.append(memory_id)
                    count += 1
                
                progress.update(task, completed=1)
                
            elif file_ext == '.csv':
                # Import from CSV
                task = progress.add_task("[cyan]Importing memories from CSV...", total=1)
                
                with open(file_path, 'r', newline='') as f:
                    reader = csv.reader(f)
                    
                    # Skip header if needed
                    if not args.no_header:
                        next(reader)
                    
                    count = 0
                    for row in reader:
                        if len(row) >= 1:
                            # Assume first column is content
                            content = row[0]
                            
                            # Create memory builder
                            builder = MemoryBuilder()
                            builder.set_content(content)
                            
                            # Set tags if provided
                            if args.tags:
                                builder.set_tags(args.tags)
                            
                            # Set importance if provided
                            if args.importance is not None:
                                builder.set_importance(args.importance)
                            
                            # Set source
                            builder.set_source(f"CSV import: {file_path}")
                            
                            # Build memory
                            memory = builder.build()
                            
                            # Add to system
                            memory_id = memcore.add_memory(memory, encrypted=args.encrypt)
                            memory_ids.append(memory_id)
                            count += 1
                
                progress.update(task, completed=1)
                
            else:
                # Assume it's a text file
                task = progress.add_task("[cyan]Importing memory from text file...", total=1)
                
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Create memory builder
                builder = MemoryBuilder()
                builder.set_content(content)
                
                if args.tags:
                    builder.set_tags(args.tags)
                
                if args.importance is not None:
                    builder.set_importance(args.importance)
                
                builder.set_source(file_path)
                
                # Build memory
                memory = builder.build()
                
                # Add to system
                memory_id = memcore.add_memory(memory, encrypted=args.encrypt)
                count = 1
                memory_ids = [memory_id]
                
                progress.update(task, completed=1)
        
        console.print(f"[green]Successfully added {count} memories.[/green]")
        
        if args.output:
            # Save memory IDs to output file
            with open(args.output, 'w') as f:
                json.dump(memory_ids, f, indent=2)
            console.print(f"[green]Memory IDs saved to {args.output}[/green]")
        
        return 0
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

def batch_folder_command(args):
    """Import memories from a folder of text files."""
    try:
        # Initialize MemCore
        memcore = MemCore(
            root_path=args.path,
            encryption_key=args.key
        )
        
        folder_path = args.folder
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            console.print(f"[red]Error: Folder '{folder_path}' does not exist or is not a directory.[/red]")
            return 1
        
        # Get list of files
        files_to_process = []
        
        if args.recursive:
            # Walk through directory recursively
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if file.endswith(args.extension):
                        files_to_process.append(os.path.join(root, file))
        else:
            # Just list files in the directory
            for file in os.listdir(folder_path):
                if file.endswith(args.extension):
                    files_to_process.append(os.path.join(folder_path, file))
        
        if not files_to_process:
            console.print(f"[yellow]No files with extension '{args.extension}' found in the folder.[/yellow]")
            return 0
        
        memory_ids = []
        count = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn()
        ) as progress:
            task = progress.add_task("[cyan]Importing memories from folder...", total=len(files_to_process))
            
            for file_path in files_to_process:
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Create memory builder
                    builder = MemoryBuilder()
                    builder.set_content(content)
                    builder.set_source(file_path)
                    
                    # Build memory
                    memory = builder.build()
                    
                    # Add to system
                    memory_id = memcore.add_memory(memory, encrypted=args.encrypt)
                    memory_ids.append(memory_id)
                    count += 1
                except Exception as e:
                    console.print(f"[red]Error processing file {file_path}: {str(e)}[/red]")
                
                progress.update(task, advance=1)
        
        console.print(f"[green]Successfully imported {count} memories from {args.folder}.[/green]")
        
        if args.output:
            # Save memory IDs to output file
            with open(args.output, 'w') as f:
                json.dump(memory_ids, f, indent=2)
            console.print(f"[green]Memory IDs saved to {args.output}[/green]")
        
        return 0
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

def batch_delete_command(args):
    """Delete multiple memories."""
    try:
        # Initialize MemCore
        memcore = MemCore(
            root_path=args.path,
            encryption_key=args.key
        )
        
        # Get memory IDs
        memory_ids = []
        
        if args.ids:
            # IDs provided directly
            memory_ids = args.ids
        elif args.ids_file:
            # IDs from file
            with open(args.ids_file, 'r') as f:
                memory_ids = json.load(f)
        elif args.query:
            # IDs from query
            memories = memcore.memql_query(args.query)
            memory_ids = [memory.id for memory in memories]
        
        if not memory_ids:
            console.print("[yellow]No memories to delete.[/yellow]")
            return 0
        
        # Confirm deletion
        if not args.force:
            console.print(f"[yellow]You are about to delete {len(memory_ids)} memories.[/yellow]")
            confirm = input("Are you sure you want to proceed? (y/N): ")
            if confirm.lower() != 'y':
                console.print("[yellow]Deletion cancelled.[/yellow]")
                return 0
        
        # Delete memories
        deleted_ids = []
        count = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn()
        ) as progress:
            task = progress.add_task("[cyan]Deleting memories...", total=len(memory_ids))
            
            for memory_id in memory_ids:
                try:
                    success = memcore.delete_memory(memory_id)
                    if success:
                        deleted_ids.append(memory_id)
                        count += 1
                except Exception as e:
                    console.print(f"[red]Error deleting memory {memory_id}: {str(e)}[/red]")
                
                progress.update(task, advance=1)
        
        console.print(f"[green]Successfully deleted {count} memories.[/green]")
        
        if args.output:
            # Save deleted IDs to output file
            with open(args.output, 'w') as f:
                json.dump(deleted_ids, f, indent=2)
            console.print(f"[green]Deleted memory IDs saved to {args.output}[/green]")
        
        return 0
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

def batch_export_command(args):
    """Export multiple memories."""
    try:
        # Initialize MemCore
        memcore = MemCore(
            root_path=args.path,
            encryption_key=args.key
        )
        
        # Get memory IDs
        memory_ids = []
        
        if args.ids:
            # IDs provided directly
            memory_ids = args.ids
        elif args.ids_file:
            # IDs from file
            with open(args.ids_file, 'r') as f:
                memory_ids = json.load(f)
        elif args.query:
            # IDs from query
            memories = memcore.memql_query(args.query)
            memory_ids = [memory.id for memory in memories]
        
        if not memory_ids and not args.query:
            console.print("[yellow]No memories to export.[/yellow]")
            return 0
        
        # Export memories
        memories_to_export = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn()
        ) as progress:
            task = progress.add_task("[cyan]Exporting memories...", total=len(memory_ids) if memory_ids else 1)
            
            if args.query and not memory_ids:
                # Export query results directly
                memories = memcore.memql_query(args.query)
                memories_to_export = [memory.to_dict() for memory in memories]
                progress.update(task, completed=1)
            else:
                # Export specific memories
                for memory_id in memory_ids:
                    memory = memcore.get_memory(memory_id)
                    if memory:
                        memories_to_export.append(memory.to_dict())
                    progress.update(task, advance=1)
        
        # Write to file
        with open(args.output, 'w') as f:
            json.dump(memories_to_export, f, indent=2)
        
        console.print(f"[green]Successfully exported {len(memories_to_export)} memories to {args.output}.[/green]")
        return 0
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="MemCore Command Line Interface")
    parser.add_argument("--version", action="version", version="MemCore v1.0.0")
    
    # Global options
    parser.add_argument("--path", "-p", default=".memfolder", help="Path to the memory folder")
    parser.add_argument("--key", "-k", help="Encryption key")
    
    # Subparsers
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize a new memory folder")
    init_parser.add_argument("--force", "-f", action="store_true", help="Force initialization even if folder exists")
    init_parser.set_defaults(func=init_command)
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new memory")
    add_parser.add_argument("--content", "-c", help="Memory content")
    add_parser.add_argument("--file", "-f", help="Read content from file")
    add_parser.add_argument("--tags", "-t", nargs="+", help="Tags for the memory")
    add_parser.add_argument("--importance", "-i", type=float, help="Importance score (0.0-1.0)")
    add_parser.add_argument("--source", "-s", help="Source of the memory")
    add_parser.add_argument("--encrypt", "-e", action="store_true", help="Encrypt the memory content")
    add_parser.set_defaults(func=add_command)
    
    # Get command
    get_parser = subparsers.add_parser("get", help="Get a memory by ID")
    get_parser.add_argument("id", help="Memory ID")
    get_parser.set_defaults(func=get_command)
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update a memory")
    update_parser.add_argument("id", help="Memory ID")
    update_parser.add_argument("--content", "-c", help="New memory content")
    update_parser.add_argument("--file", "-f", help="Read new content from file")
    update_parser.add_argument("--tags", "-t", nargs="+", help="New tags for the memory")
    update_parser.add_argument("--importance", "-i", type=float, help="New importance score (0.0-1.0)")
    update_parser.add_argument("--source", "-s", help="New source of the memory")
    update_parser.set_defaults(func=update_command)
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a memory")
    delete_parser.add_argument("id", help="Memory ID")
    delete_parser.add_argument("--force", "-f", action="store_true", help="Skip confirmation")
    delete_parser.set_defaults(func=delete_command)
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query memories using MemQL")
    query_parser.add_argument("query", help="MemQL query")
    query_parser.add_argument("--full", "-f", action="store_true", help="Show full memory details")
    
    query_parser.set_defaults(func=query_command)
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export memories to a JSON file")
    export_parser.add_argument("output", help="Output file path")
    export_parser.set_defaults(func=export_command)
    
    # Import command
    import_parser = subparsers.add_parser("import", help="Import memories from a JSON file")
    import_parser.add_argument("input", help="Input file path")
    import_parser.add_argument("--encrypt", "-e", action="store_true", help="Encrypt imported memories")
    import_parser.set_defaults(func=import_command)
    
    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create a backup of the memory system")
    backup_parser.set_defaults(func=backup_command)
    
    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore from a backup")
    restore_parser.add_argument("backup", help="Backup directory path")
    restore_parser.set_defaults(func=restore_command)
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Start the MemCore server")
    server_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    server_parser.add_argument("--port", "-p", type=int, default=8000, help="Port to listen on")
    server_parser.set_defaults(func=server_command)
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show statistics about the memory system")
    stats_parser.set_defaults(func=stats_command)
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all memories")
    list_parser.add_argument("--tag", "-t", help="Filter by tag")
    list_parser.add_argument("--sort", "-s", choices=["importance", "created", "updated"], help="Sort field")
    list_parser.add_argument("--desc", "-d", action="store_true", help="Sort in descending order")
    list_parser.add_argument("--limit", "-l", type=int, help="Limit number of results")
    list_parser.add_argument("--full", "-f", action="store_true", help="Show full memory details")
    list_parser.set_defaults(func=list_command)
    
    # History command
    history_parser = subparsers.add_parser("history", help="Show the history of a memory")
    history_parser.add_argument("id", help="Memory ID")
    history_parser.add_argument("--full", "-f", action="store_true", help="Show full history details")
    history_parser.set_defaults(func=history_command)
    
    # Batch commands
    batch_subparsers = subparsers.add_parser("batch", help="Batch operations")
    batch_commands = batch_subparsers.add_subparsers(dest="batch_command", help="Batch command to execute")
    
    # Batch add command
    batch_add = batch_commands.add_parser("add", help="Add multiple memories from a file")
    batch_add.add_argument("file", help="Input file (JSON, CSV, or text)")
    batch_add.add_argument("--encrypt", "-e", action="store_true", help="Encrypt the memories")
    batch_add.add_argument("--tags", "-t", nargs="+", help="Tags for text file import")
    batch_add.add_argument("--importance", "-i", type=float, help="Importance for text file import")
    batch_add.add_argument("--no-header", action="store_true", help="CSV file has no header")
    batch_add.add_argument("--output", "-o", help="Output file for memory IDs")
    batch_add.set_defaults(func=batch_add_command)
    
    # Batch folder command
    batch_folder = batch_commands.add_parser("folder", help="Import memories from a folder of text files")
    batch_folder.add_argument("folder", help="Folder containing text files")
    batch_folder.add_argument("--encrypt", "-e", action="store_true", help="Encrypt the memories")
    batch_folder.add_argument("--recursive", "-r", action="store_true", help="Search recursively in subfolders")
    batch_folder.add_argument("--extension", default=".txt", help="File extension to look for")
    batch_folder.add_argument("--output", "-o", help="Output file for memory IDs")
    batch_folder.set_defaults(func=batch_folder_command)
    
    # Batch delete command
    batch_delete = batch_commands.add_parser("delete", help="Delete multiple memories")
    batch_delete.add_argument("--ids", nargs="+", help="Memory IDs to delete")
    batch_delete.add_argument("--ids-file", help="File containing memory IDs")
    batch_delete.add_argument("--query", help="MemQL query to select memories")
    batch_delete.add_argument("--force", "-f", action="store_true", help="Skip confirmation")
    batch_delete.add_argument("--output", "-o", help="Output file for deleted memory IDs")
    batch_delete.set_defaults(func=batch_delete_command)
    
    # Batch export command
    batch_export = batch_commands.add_parser("export", help="Export multiple memories")
    batch_export.add_argument("output", help="Output file path")
    batch_export.add_argument("--ids", nargs="+", help="Memory IDs to export")
    batch_export.add_argument("--ids-file", help="File containing memory IDs")
    batch_export.add_argument("--query", help="MemQL query to select memories")
    batch_export.set_defaults(func=batch_export_command)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Show help if no command specified
    if not args.command:
        parser.print_help()
        return 0
    
    # Execute command
    return args.func(args)

if __name__ == "__main__":
    sys.exit(main())
