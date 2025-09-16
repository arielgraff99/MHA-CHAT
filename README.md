# TimelineNarrator

A web application that extracts information from emails, text files, PDFs, and images, then generates timeline-based narratives with source traceability.

## Features

- **Multi-format ingestion**: Supports emails (.eml, .msg), text files (.txt, .md, .csv, .json), PDFs, and images
- **AI-powered extraction**: Uses OCR for images and PDFs, RFC 5322 parsing for emails
- **Timeline generation**: Creates chronological timelines with customizable resolution (hours to years)
- **Narrative synthesis**: Generates coherent narratives with full source attribution
- **Entity extraction**: Identifies people, organizations, locations, dates, and keywords
- **Source traceability**: Every claim links back to original source documents
- **PII protection**: Automatic detection and masking of sensitive information
- **Export capabilities**: CSV exports and downloadable data bundles

## Architecture

### Backend (Python/FastAPI)
- **API Layer**: FastAPI with automatic OpenAPI documentation
- **Extractors**: Modular extractors for different file types
- **NLP Pipeline**: spaCy for entity extraction, OpenAI for narrative generation
- **Database**: SQLAlchemy with PostgreSQL/SQLite support
- **Security**: PII masking, encryption, audit logging

### Frontend (React/TypeScript)
- **Modern UI**: React with Tailwind CSS and Framer Motion animations
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Progress**: Live updates during processing
- **Interactive Timeline**: Clickable events with detailed views
- **Source Navigation**: Click source references to view details

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL (optional, SQLite works for development)
- Tesseract OCR (for image/PDF text extraction)

### Installation

1. **Clone and setup backend:**
```bash
# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python -c "from backend.models.database import create_tables; create_tables()"
```

2. **Setup frontend:**
```bash
# Install Node.js dependencies
npm install

# Build frontend
npm run build
```

3. **Install system dependencies:**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Download spaCy model
python -m spacy download en_core_web_sm
```

### Running the Application

1. **Start the backend server:**
```bash
python run_backend.py
```

2. **For development, start frontend separately:**
```bash
npm start
```

The application will be available at:
- Backend API: http://localhost:8000
- Frontend: http://localhost:3000 (development) or http://localhost:8000 (production)
- API Documentation: http://localhost:8000/docs

## Usage

### 1. Investigation Setup
- Define what you want to investigate (person, event, topic)
- AI will refine your brief and ask for confirmation
- Set temporal boundaries (start/end dates)
- Choose timeline resolution (hours, days, weeks, months, years)

### 2. File Upload
- Drag & drop or select source documents
- Supports multiple file formats
- Real-time validation and progress tracking

### 3. Processing Pipeline
The application processes your files through five stages:
1. **Ingestion**: Upload and validate files
2. **Extraction**: Extract text using appropriate methods
3. **Normalization**: Detect dates, entities, and normalize timestamps
4. **Aggregation**: Create timeline events and deduplicate
5. **Narrative**: Generate coherent narrative with source attribution

### 4. Results
- **Timeline View**: Interactive chronological timeline
- **Table View**: Sortable table of all events
- **Narrative View**: Generated narrative with clickable source references
- **Export**: Download CSV files and complete data bundle

## API Endpoints

- `POST /ingest`: Upload files and get source IDs
- `POST /extract`: Extract text from uploaded files
- `POST /events`: Generate timeline events
- `POST /narrative`: Generate narrative from events
- `GET /download`: Download complete data bundle
- `POST /refine-brief`: Refine investigation brief with AI
- `GET /health`: Health check endpoint

## Data Export

The application exports three CSV files:

1. **extracted_text_{timestamp}.csv**: Raw extracted text from all sources
2. **events_{timestamp}.csv**: Timeline events with entities and metadata
3. **narrative_{timestamp}.csv**: Generated narrative blocks with source attribution

Each export includes:
- Schema documentation (schema_readme.md)
- Provenance manifest (provenance_manifest.json)
- Complete audit trail

## Configuration

Key environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/timeline_narrator

# AI/NLP
OPENAI_API_KEY=your-openai-api-key
SPACY_MODEL=en_core_web_sm

# File Storage
MAX_FILE_SIZE_MB=250
MAX_TOTAL_SIZE_GB=5

# Security
ENCRYPTION_KEY=your-encryption-key
SECRET_KEY=your-secret-key

# Timezone
DEFAULT_TIMEZONE=America/Toronto
```

## Security Features

- **PII Protection**: Automatic detection and masking of emails, phone numbers, SSNs
- **Encryption**: Sensitive data encrypted at rest
- **Audit Logging**: Complete audit trail of all operations
- **File Validation**: MIME type validation and size limits
- **Source Attribution**: Every narrative claim traceable to original sources

## Development

### Backend Development
```bash
# Run with auto-reload
python run_backend.py

# Run tests
python -m pytest

# Database migrations
alembic upgrade head
```

### Frontend Development
```bash
# Start development server
npm start

# Run tests
npm test

# Build for production
npm run build
```

## Troubleshooting

### Common Issues

1. **OCR not working**: Install Tesseract OCR system package
2. **spaCy model missing**: Run `python -m spacy download en_core_web_sm`
3. **Database connection**: Check DATABASE_URL in .env file
4. **File upload fails**: Check file size limits and supported formats
5. **OpenAI API errors**: Verify OPENAI_API_KEY is set correctly

### Logs
- Application logs: Check console output
- Audit logs: `logs/audit.log`
- Error details: Available in API responses

## License

Copyright © 2024 TimelineNarrator. All rights reserved.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review API documentation at `/docs`
3. Check application logs for detailed error messages
