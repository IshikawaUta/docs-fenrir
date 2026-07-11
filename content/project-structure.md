# Project Structure

For best practices, here's the recommended folder structure for a Fenrir project:

```text
my_fenrir_app/
│
├── app.py                  # Main application file
├── requirements.txt        # Python dependencies
├── README.md              # Project documentation
├── .gitignore             # Git configuration
│
├── templates/             # HTML templates folder
│   ├── index.html         # Home page
│   ├── base.html          # Base template (for inheritance)
│   ├── 404.html           # Custom 404 page
│   ├── 500.html           # Custom 500 page
│   └── blog/              # Subfolder for specific templates
│       ├── list.html
│       └── detail.html
│
├── static/                # Static files folder
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── script.js
│   ├── images/
│   └── favicon.ico
│
├── routes/                # Routes organization
│   ├── __init__.py
│   ├── users.py
│   ├── products.py
│   └── api.py
│
├── models/                # Pydantic models
│   ├── __init__.py
│   ├── user.py
│   └── product.py
│
├── utils/                 # Utility functions
│   ├── __init__.py
│   ├── validators.py
│   └── helpers.py
│
├── tests/                 # Test cases
│   ├── __init__.py
│   ├── test_routes.py
│   ├── test_models.py
│   └── conftest.py        # Pytest configuration
│
└── uploads/               # File uploads (optional)
```

### Structure Explanation:

- **app.py**: Main file containing Fenrir application initialization
- **templates/**: All Jinja2 HTML files stored here
- **static/**: CSS, JavaScript, and images stored here
- **routes/**: Blueprints and route handlers organized in separate files
- **models/**: Pydantic models for data validation
- **utils/**: Helper functions and custom validators
- **tests/**: Unit tests and integration tests
- **uploads/**: Folder for storing user-uploaded files

### Example requirements.txt:

```text
fenrir-framework==4.1.2
pydantic==2.0.0
jinja2==3.0.0
asteri>=2.2.2
pytest==7.4.0
pytest-asyncio==0.21.0
python-multipart==0.0.18
```
