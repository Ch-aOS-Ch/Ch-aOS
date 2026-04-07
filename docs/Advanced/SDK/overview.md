# The Ch-aOS SDK: Beyond the CLI

So, the CLI is cool and all. You can apply roles, manage secrets, and write encrypted rambles. But what if you are building an internal platform? What if you want to write a custom Python script that orchestrates your infrastructure, but you still want the power of Ch-aOS's declarative roles, secret providers, and telemetry?

Well, you are in luck! Ch-aOS is built API-first. Everything the CLI does is actually just instantiating Data Transfer Objects (DTOs) called `Payloads` and passing them to our library functions, which then return a standardized `ResultPayload`.

This means you can import `chaos` into your own Python code and use it as a Software Development Kit (SDK).

Let it be known: The Ch-aOS SDK is not just a wrapper around the CLI. It's a fully featured API that gives you direct access to all the core functionality of Ch-aOS, without any of the overhead of subprocess calls or CLI parsing. It is THE most powerful way to use Ch-aOS, and with great power comes great responsibility. The SDK is designed to be blazing fast (at least for a Python based SDK) and highly predictable, but it also means you need to understand the core concepts of how it works to use it effectively.

It is quite fast overall, it uses lots and lots of lazy loading and optimization tricks to minimize startup and import times, but it is not a silver bullet. Since it uses lazy loading, for instance, the first call to a specific function might be a bit slower than subsequent calls because it needs to load its own imports and dependencies. But once it's loaded, it should be very fast, I personally recommend that, for long-running applications, you do an "warm up" call to the SDK right after importing it, just to load all the dependencies and ensure that subsequent calls are as fast as possible.

It is THE advanced of all of Ch-aOS's advanced features, and, while being the gateway for you to build your own custom platforms and tools, it is inherently far more complex than the CLI. So, if you are new to Ch-aOS, I recommend starting with the CLI and then diving into the SDK once you are comfortable with the core concepts.

## The Core Philosophy: Payloads and Results

To keep things blazing fast and highly predictable, the Ch-aOS SDK relies on two main concepts for its API:

### 1. Request Payloads (DTOs)
Instead of functions with 20 arguments, we pass Payload objects. These are highly optimized classes (using `__slots__` for instant startup times) that hold all the configuration needed for an operation.

For example, if you want to read a Ramble programmatically, you don't pass a bunch of strings, you pass a `RambleReadPayload`.

I can already tell you're thinking about the overhead of creating these objects, but don't fret! These were designed to be as lightweight as possible, without that many drawbacks, they are NOT @dataclasses, nor do they use `__dict__` for attribute storage. Rather, all of them have a `to_dict()` and a `from_dict(dict)` method, so you can easily serialize and deserialize them if you want to store them or pass them around. They also have a `__repr__` method that makes debugging a breeze.

These were hand-made and hand-optimized for performance, I measured them myself against regular dataclasses. The main issue with these is that they are not very flexible, since they don't allow for dynamic attributes, but hey, not a biggie, we don't need that for our use case!

### 2. The `ResultPayload`
Every major function in the SDK returns a `ResultPayload`. This is our standardized contract. It guarantees you will never have to guess how to handle a response or catch random, undocumented exceptions.

A `ResultPayload` looks like this:
```python
class ResultPayload(Generic[T]):
    success: bool            # Did the operation succeed?
    message: list[str]       # Human-readable messages or warnings
    data: T | None           # The actual output data (if any)
    error: list[str]         # What went wrong?
```

This makes error handling a breeze!

```python
from chaos.lib.ramble import handleReadRamble
from chaos.lib.args.dataclasses import RambleReadPayload, SecretsContext

# Set up our context
context = SecretsContext(team="my_company.my_team.dex")
payload = RambleReadPayload(targets=["journal.page"], context=context)

# Call the SDK
result = handleReadRamble(payload)

if not result.success:
    for err in result.error:
        print(f"Oh no! Error: {err}")
else:
    print("Here is your ramble data:")
    print(result.data)
```

## What can you do with the SDK?

Literally everything the CLI can do.
- **Secrets Management**: Decrypt files, rotate keys, and integrate with password managers via the `chaos.lib.secrets` and `chaos.lib.secret_backends` modules.

- **Orchestration**: Run Pyinfra operations, calculate deltas, and apply state via `chaos.lib.apply`.

- **Rambles**: Read, write, search, and manage encrypted notes via `chaos.lib.ramble`.

- **etc, etc, etc**: Other than `chaos set` and `chaos init secrets`, which are basically just helpers for bootstrapping, every single CLI command has a corresponding `handle_*` function in the SDK that you can call directly.

Dive into the other sections to learn how to orchestrate infrastructure directly from your Python code!
