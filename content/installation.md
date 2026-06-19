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

- `redis>=4.0.0` — Required for `RedisSessionInterface` and distributed rate limiting
