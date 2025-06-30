import os
import sys
import time
import platform
import random
import psutil
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel
from rich import box
from memco import MemCore, MemoryBuilder
from memco.embedding import get_embedding_provider
import torch
console = Console()

def print_env_and_system_info():
    console.rule("[bold blue]Environment & System Info")
    table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE)
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    # Environment variables (show a few common ones)
    for key in ["USER", "USERNAME", "COMPUTERNAME", "HOME", "PATH"]:
        val = os.environ.get(key, "N/A")
        table.add_row(key, val)
    # System info
    table.add_row("OS", platform.platform())
    table.add_row("Python", sys.version.replace("\n", " "))
    table.add_row("CPU", platform.processor())
    table.add_row("CPU Cores", str(psutil.cpu_count(logical=True)))
    table.add_row("RAM (GB)", f"{psutil.virtual_memory().total / (1024**3):.2f}")
    table.add_row("Disk Space (GB)", f"{psutil.disk_usage('/').total / (1024**3):.2f}")

    console.print(table)
    embedding_table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE)
    embedding_table.add_column("Key", style="cyan", no_wrap=True)
    embedding_table.add_column("Value", style="white")
    embedding_provider = get_embedding_provider()
    embedding_name = embedding_provider.get_name()
    if embedding_name == "OpenAI":
        console.rule("[bold blue]OpenAI Info")
        conf = embedding_provider.get_config()
        embedding_table.add_row("Embedding Model", conf.get("model", "N/A"))
        embedding_table.add_row("OpenAI Org", conf.get("organization", "N/A"))
        embedding_table.add_row("OpenAI API Base", conf.get("api_base", "N/A"))
        api_key = conf.get("api_key")
        embedding_table.add_row("OpenAI API Key", (api_key[:8] + "..." if api_key else "N/A"))
    elif embedding_name == "Cohere":
        console.rule("[bold blue]Cohere Info")
        conf = embedding_provider.get_config()
        embedding_table.add_row("Embedding Model", conf.get("model", "N/A"))
        api_key = conf.get("api_key")
        embedding_table.add_row("Cohere API Key", (api_key[:8] + "..." if api_key else "N/A"))
    elif embedding_name == "Transformer":
        console.rule("[bold blue]Transformer Info")
        conf = embedding_provider.get_config()
        embedding_table.add_row("Transformer Model", conf.get("model_name", "N/A"))
        if torch.cuda.is_available():
            embedding_table.add_row("GPU", torch.cuda.get_device_name(0))
            embedding_table.add_row("GPU Memory (GB)", f"{torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f}")
        else:
            embedding_table.add_row("GPU", "N/A")
    console.print(embedding_table)

def print_step(msg):
    console.print(f"[bold green]➤ {msg}")

def print_substep(msg):
    console.print(f"[yellow]  • {msg}")

def pretty_summary(stats):
    console.rule("[bold blue]Performance Summary")
    table = Table(show_header=True, header_style="bold green", box=box.ROUNDED)
    table.add_column("Step", style="cyan")
    table.add_column("Time (s)", style="magenta")
    for step, t in stats.items():
        table.add_row(step, f"{t:.2f}")
    console.print(table)

def print_final_panel():
    panel = Panel.fit(
        "[bold green]All performance tests completed successfully! :rocket:\n"
        "[bold blue]Check 'memories_perf_backup.json' for exported data.",
        title="[bold yellow]Done",
        border_style="bright_magenta"
    )
    console.print(panel)

# --- Script starts here ---
print_env_and_system_info()

embedding_provider = get_embedding_provider()
mem_system = MemCore(
    root_path=".memfolder",
    encryption_key="my_secret_key",
    embedding_provider=embedding_provider
)
builder = MemoryBuilder(embedding_provider)
NUM_MEMORIES = 500

random_tags = ["cool", "awesome", "coding", "python", "test", "memories", "fantastic", "vector", "search", "performance","cookies","cakes","ice cream","chocolate","sweets","candy","snacks","food"]
random_phrase_parts = [
    [
        "AI", "Machine Learning", "Deep Learning", "Neural Networks", "Natural Language Processing",
        "Cooking", "Dancing", "Fighting", "Baking", "Singing", "Painting", "Gardening", "Swimming",
        "Running", "Chess", "Boxing", "Karate", "Salsa", "Grilling", "Roasting", "Juggling"
    ],
    [
        "improves", "enhances", "accelerates", "transforms", "optimizes", "inspires", "challenges",
        "teaches", "motivates", "empowers", "stimulates", "enriches", "elevates", "tests", "trains"
    ],
    [
        "search", "recommendation", "classification", "prediction", "automation", "recipes",
        "choreography", "combat", "strategy", "performance", "competition", "routine", "presentation",
        "preparation", "training", "tournament", "battle", "routine", "showdown", "exhibition"
    ],
    [
        "systems", "applications", "platforms", "solutions", "tools", "kitchens", "stages", "arenas",
        "studios", "rings", "fields", "gyms", "gardens", "pools", "tracks", "boards", "venues"
    ],
    [
        "for", "in", "with", "using", "through", "during", "while", "alongside", "amidst", "among"
    ],
    [
        "Python", "JavaScript", "Rust", "Go", "C++", "spices", "music", "martial arts", "flavors",
        "beats", "colors", "plants", "water", "speed", "logic", "moves", "techniques", "styles"
    ],
    [
        "developers", "engineers", "researchers", "scientists", "analysts", "chefs", "dancers",
        "fighters", "artists", "athletes", "musicians", "painters", "gardeners", "swimmers",
        "runners", "players", "performers", "trainers"
    ],
    [
        "quickly", "efficiently", "reliably", "securely", "scalably", "creatively", "gracefully",
        "powerfully", "smoothly", "boldly", "precisely", "delicately", "vigorously", "elegantly"
    ],
    [
        "today", "now", "in 2024", "for the future", "at scale", "every night", "in tournaments",
        "at home", "on stage", "in the ring", "in the kitchen", "in the studio", "on the field",
        "in the garden", "in the pool", "on the track"
    ],
    [
        "memories", "vectors", "embeddings", "data", "knowledge", "meals", "moves", "matches",
        "paintings", "songs", "dishes", "routines", "battles", "games", "performances"
    ],
    [
        "performance", "accuracy", "speed", "robustness", "usability", "taste", "rhythm", "strength",
        "creativity", "endurance", "style", "technique", "flavor", "expression", "agility"
    ]
]

def generate_random_phrase(parts):
    return " ".join([random.choice(part) for part in parts])

stats = {}

print_step(f"Creating {NUM_MEMORIES} memories one by one...")
memory_ids = []
start = time.time()
with Progress(
    SpinnerColumn(), BarColumn(), "[progress.percentage]{task.percentage:>3.0f}%", TimeElapsedColumn(), console=console
) as progress:
    task = progress.add_task("[cyan]Adding memories...", total=NUM_MEMORIES)
    for i in range(NUM_MEMORIES):
        memory = builder.set_content(f"Memory {i}: {generate_random_phrase(random_phrase_parts)}") \
                        .set_tags(["1x1", f"tag{i%10}", random_tags[i % len(random_tags)]]) \
                        .set_importance(0.5 + (i % 10) * 0.05) \
                        .set_source("perf.test.py") \
                        .build()
        memory_id = mem_system.add_memory(memory, encrypted=False)
        memory_ids.append(memory_id)
        progress.update(task, advance=1)
end = time.time()
stats["One by one creation"] = end - start
print_substep(f"Created {NUM_MEMORIES} memories.")

print_step(f"Creating {NUM_MEMORIES} memories in bulk (object creation)...")
memories = []
start = time.time()
with Progress(
    SpinnerColumn(), BarColumn(), "[progress.percentage]{task.percentage:>3.0f}%", TimeElapsedColumn(), console=console
) as progress:
    task = progress.add_task("[cyan]Building memory objects...", total=NUM_MEMORIES)
    for i in range(NUM_MEMORIES):
        mem = builder.set_content(f"Memory {i}: {generate_random_phrase(random_phrase_parts)}") \
            .set_tags(["1x1", f"tag{i%10}", random_tags[i % len(random_tags)]]) \
            .set_importance(0.5 + (i % 10) * 0.05) \
            .set_source("perf.test.py") \
            .build()
        memories.append(mem)
        progress.update(task, advance=1)
end = time.time()
stats["Bulk object creation"] = end - start
print_substep(f"Memory objects created: {len(memories)}")

console.print("[bold cyan]Sample memories:")
for idx, mem in enumerate(memories[:5]):
    console.print(f"[{idx}] id: {id(mem)} content: {mem.content}")

print_step("Adding memories in bulk to system...")
start = time.time()
mem_system.add_bulk_memories(memories, encrypted=False)
end = time.time()
stats["Bulk add"] = end - start

print_step(f"Fetching {NUM_MEMORIES} memories...")
start = time.time()
with Progress(
    SpinnerColumn(), BarColumn(), "[progress.percentage]{task.percentage:>3.0f}%", TimeElapsedColumn(), console=console
) as progress:
    task = progress.add_task("[cyan]Fetching memories...", total=NUM_MEMORIES)
    fetched = []
    for mid in memory_ids:
        fetched.append(mem_system.get_memory(mid))
        progress.update(task, advance=1)
end = time.time()
stats["Bulk fetch"] = end - start

print_step("Vector search performance test:")
search_queries = ["AI", "vector", "test", "tag5"]
for query in search_queries:
    start = time.time()
    results = mem_system.vector_search_query(query, top_k=5)
    end = time.time()
    stats[f"Vector search '{query}'"] = end - start
    console.print(f"[bold magenta]Query '{query}'[/] - {len(results)} results in [green]{end - start:.4f}[/] seconds")

print_step("MemQL performance test:")
start = time.time()
results = mem_system.memql_query('SELECT WHERE tags == "tag5" ORDER BY importance DESC')
end = time.time()
stats["MemQL query"] = end - start
console.print(f"[bold magenta]MemQL query[/] returned {len(results)} results in [green]{end - start:.4f}[/] seconds")

print_step("Exporting to JSON...")
start = time.time()
mem_system.export_json("memories_perf_backup.json")
end = time.time()
stats["Export"] = end - start
print_substep("Exported to 'memories_perf_backup.json'.")

mem_system.close()
pretty_summary(stats)
print_final_panel()
