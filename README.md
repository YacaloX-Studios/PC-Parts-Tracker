# PC Parts Tracker

Desktop application for tracking PC component prices from MercadoLibre Colombia. Built as a replacement for spreadsheet-based price tracking, with support for price history, PC build management, and Excel import/export.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

---

## Features

- **Price Tracking** — Monitor current prices for CPU, GPU, RAM, SSD, Motherboard, PSU, Case, Cooler, Monitor, and peripherals
- **MercadoLibre API** — Official API integration with OAuth2 authentication for reliable price lookups
- **Excel Import** — Import your existing product catalog from Excel spreadsheets (.xlsm, .xlsx)
- **Manual Price Entry** — Spreadsheet-like interface for entering prices manually
- **Price History** — Track price changes over time with interactive charts
- **PC Builds** — Create and manage full PC configurations, calculate totals and savings
- **Product Management** — Add, edit, and organize components by category
- **URL Direct Access** — Open product pages directly in your browser
- **Export** — Export your data to Excel or CSV
- **Dark Mode** — Modern UI with CustomTkinter (dark/light/system themes)

## Architecture

```
pc-parts-tracker/
├── main.py                 # Entry point
├── database/               # SQLAlchemy ORM models & connection
├── repositories/           # Data access layer (CRUD)
├── providers/              # Price fetching (API, scraper, JSON)
├── services/               # Business logic
├── gui/                    # CustomTkinter desktop UI
├── utils/                  # Config, logging, caching, Excel I/O
├── tests/                  # Unit tests
└── data/                   # Runtime data (gitignored)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.10+ |
| GUI | CustomTkinter |
| Database | SQLite via SQLAlchemy 2.0 |
| API | MercadoLibre REST API (OAuth2) |
| Scraping | Playwright + Chromium (optional) |
| Charts | Matplotlib |
| Excel I/O | openpyxl + pandas |
| Icons | Pillow |

## Installation

### Prerequisites

- Python 3.10 or higher
- pip

### Steps

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/pc-parts-tracker.git
cd pc-parts-tracker
```

2. **Create a virtual environment** (recommended)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Install Playwright browsers** (only needed if using scraping)

```bash
playwright install chromium
```

5. **Run the application**

```bash
python main.py
```

## Usage

### First Run

On first launch, the application will detect if you have an existing Excel spreadsheet and offer to import your products automatically.

### Importing from Excel

1. Click **Importar Excel** in the toolbar
2. Select your `.xlsm` or `.xlsx` file
3. Products are imported with names, categories, URLs, and prices

### Entering Prices Manually

1. Click **Ingresar Precios**
2. Enter prices in the spreadsheet-like interface
3. Click **Guardar Todos**

### Setting Up MercadoLibre API

1. Register an app at [developers.mercadolibre.com](https://developers.mercadolibre.com)
2. Go to **Settings** in the application
3. Enter your `client_id` and `client_secret`
4. Click **Sesion ML** to authorize
5. Use **Actualizar Precios** to fetch current prices

### Managing PC Builds

1. Click **Builds** in the toolbar
2. Create a new build and add products
3. View totals and track savings

### Viewing Price History

Double-click any product or click **Ver Historial** to see price trends with interactive charts.

## Configuration

The application stores settings in `config.json`:

```json
{
  "appearance_mode": "dark",
  "cache_ttl_minutes": 60,
  "default_currency": "COP",
  "browser_headless": true,
  "backup_on_exit": true
}
```

API credentials (`ml_client_id`, `ml_client_secret`) are stored separately in `config.json` and should never be committed to version control.

## Project Structure

| Module | Description |
|--------|------------|
| `database/` | SQLAlchemy models and SQLite connection manager |
| `repositories/` | Repository pattern for data access |
| `providers/` | Pluggable price providers (API, scraper, JSON) |
| `services/` | Business logic for price updates, builds, notifications |
| `gui/` | CustomTkinter windows and dialogs |
| `utils/` | Configuration, logging, caching, Excel utilities |
| `tests/` | Unit tests with pytest |

## Running Tests

```bash
python -m pytest tests/ -v
```

## Screenshots

<!-- Add screenshots here -->
<!-- ![Main Window](screenshots/main.png) -->
<!-- ![Price History](screenshots/history.png) -->
<!-- ![Build Manager](screenshots/builds.png) -->

## Roadmap

- [ ] Price drop notifications (Discord, Email)
- [ ] Multi-store support (Amazon, Falabella)
- [ ] Price alerts with target prices
- [ ] CSV/PDF export
- [ ] Cross-platform support (macOS, Linux)
- [ ] Web dashboard

## Contributing

Contributions are welcome. Please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — Modern UI framework
- [SQLAlchemy](https://www.sqlalchemy.org/) — Database toolkit
- [MercadoLibre API](https://developers.mercadolibre.com/) — Product data
- [Playwright](https://playwright.dev/python/) — Browser automation
