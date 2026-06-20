# Installation

### From PyPI (Recommended)

```bash
pip install fenrir-framework
```

### Development Installation

```bash
git clone https://github.com/IshikawaUta/fenrir.git
cd fenrir
pip install -e .
```

### Requirements

- Python 3.8 or higher
- `pydantic>=2.0.0`
- `jinja2>=3.0.0`
- `asteri>=2.2.2`
- `itsdangerous>=2.0.0`
- `python-multipart>=0.0.18`
- `typing_extensions>=4.0.0`
- `bcrypt>=4.0.0`
- `python-dotenv>=1.0.0`

### Optional Dependencies

**Redis Support** — For distributed sessions and rate limiting:

```bash
pip install fenrir-framework[redis]
```

Includes: `redis>=4.0.0`

**ORM SQLite Support** — For lightweight async ORM with SQLite:

```bash
pip install fenrir-framework[sqlite]
```

Includes: `aiosqlite>=0.19.0`

**ORM PostgreSQL Support** — For async ORM with PostgreSQL:

```bash
pip install fenrir-framework[postgresql]
```

Includes: `asyncpg>=0.29.0`

**ORM Full Support** — For both SQLite and PostgreSQL:

```bash
pip install fenrir-framework[orm]
```

Includes: `aiosqlite>=0.19.0`, `asyncpg>=0.29.0`

**GraphQL Support** — For GraphQL API with Strawberry:

```bash
pip install fenrir-framework[graphql]
```

Includes: `strawberry-graphql>=0.200.0`

**gRPC Support** — For gRPC services:

```bash
pip install fenrir-framework[grpc]
```

Includes: `grpcio>=1.58.0`, `grpcio-health-checking>=1.58.0`

**All Optional Dependencies** — Install everything:

```bash
pip install fenrir-framework[all]
```
