# Fenrir Documentation Portal

This repository contains the source code and Markdown content for the official documentation website of the **Fenrir Web Framework** (v3.1.2). 

The portal is built as a lightweight, high-performance web application powered by **Fenrir** and the **Asteri** ASGI server. It dynamically parses and renders Markdown documentation pages on the fly, offering full-text search, clean sidebar navigation, and a modern responsive user interface.

---

## Features

- ⚡ **Dynamic Rendering**: Documentation pages are written in standard Markdown (`.md`) inside the `content/` folder and rendered dynamically using Python's `markdown` library and Jinja2 templates.
- 🔍 **Local Search API**: Features an in-memory full-text search endpoint (`/api/search`) to query documentation headers and content instantly.
- 📐 **Clean Responsive Design**: Modern sidebar layout built using Tailwind CSS and Lucide Icons, fully responsive across mobile, tablet, and desktop screens.
- 🦊 **Powered by Fenrir**: The portal runs on Fenrir v3.1.2 itself, showcasing its capabilities in a production-ready setup.

---

## Directory Structure

```text
docs-fenrir/
├── content/              # Markdown documentation files (.md)
├── static/               # Static assets (CSS, JS, images, favicon)
│   ├── css/
│   ├── js/
│   └── images/
├── templates/            # Jinja2 HTML templates
│   └── layout.html       # Base page layout and layout structure
├── app.py                # Main application script
├── requirements.txt      # Project dependencies
├── LICENSE               # MIT License
└── README.md             # Project documentation
```

---

## Installation & Setup

### Prerequisites

- Python 3.8 to 3.13
- Pip (Python package installer)

### 1. Clone the Repository

```bash
git clone https://github.com/IshikawaUta/docs-fenrir.git
cd docs-fenrir
```

### 2. Set Up a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

Install the required packages listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## Local Development

Start the development server with auto-reload enabled:

```bash
fenrir run app:app --port 8000 --dev
```

Once running, you can access the documentation portal locally at:
**[http://localhost:8000](http://localhost:8000)**

---

## Writing Documentation

To add or update documentation pages:

1. **Create or edit Markdown files**: Modify the `.md` files inside the `content/` directory.
2. **Update sidebar navigation**: If you add a new page, add it to the page navigation layout configuration in `app.py` under the routing registry so it appears in the sidebar automatically.
3. **Write in clean Markdown**: Use standard Markdown syntax. Code blocks with language specifiers are automatically syntax-highlighted using Pygments styling.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
