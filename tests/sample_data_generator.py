"""
Sample Data Generator for TimelineNarrator Testing

This module creates realistic sample data files for testing all supported file types:
- Email files (.eml, .msg)
- Text documents (.txt, .md, .csv, .json)
- PDF documents (.pdf)
- Images (.jpg, .png, .tiff) with text content for OCR

Usage:
    python tests/sample_data_generator.py
    
Or import and use programmatically:
    from tests.sample_data_generator import SampleDataGenerator
    generator = SampleDataGenerator()
    files = generator.generate_all_samples()
"""

import os
import json
import csv
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
from PIL import Image, ImageDraw, ImageFont
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import tempfile
import uuid

class SampleDataGenerator:
    """Generates comprehensive sample data for testing TimelineNarrator"""
    
    def __init__(self, output_dir: str = "tests/sample_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        for subdir in ["emails", "documents", "pdfs", "images"]:
            (self.output_dir / subdir).mkdir(exist_ok=True)
    
    def generate_all_samples(self) -> Dict[str, List[str]]:
        """Generate all sample files and return paths organized by type"""
        files = {
            "emails": self.generate_email_samples(),
            "documents": self.generate_document_samples(),
            "pdfs": self.generate_pdf_samples(),
            "images": self.generate_image_samples()
        }
        
        print(f"📁 Generated {sum(len(v) for v in files.values())} sample files in {self.output_dir}")
        return files
    
    def generate_email_samples(self) -> List[str]:
        """Generate various email file samples"""
        files = []
        
        # Sample 1: Basic business email
        email1 = self._create_email(
            from_addr="john.doe@company.com",
            to_addr="jane.smith@company.com",
            subject="Project Timeline Update",
            date=datetime(2024, 1, 15, 9, 30),
            body="""Hi Jane,

I wanted to update you on the project timeline. We've completed phase 1 ahead of schedule.

Key milestones:
- Requirements gathering: Completed Jan 10, 2024
- Design phase: Started Jan 12, 2024
- Development kickoff: Scheduled for Jan 20, 2024

The team includes:
- John Doe (Project Manager)
- Sarah Wilson (Lead Developer) 
- Mike Chen (QA Engineer)

Location: Main office, New York
Contact: john.doe@company.com

Best regards,
John Doe
Project Manager
Company Inc.
Phone: (555) 123-4567
"""
        )
        files.append(self._save_email(email1, "emails/business_update.eml"))
        
        # Sample 2: Email with attachments and multiple recipients
        email2 = self._create_email(
            from_addr="legal@lawfirm.com",
            to_addr="client@company.com",
            cc_addr="paralegal@lawfirm.com",
            subject="Contract Review - URGENT",
            date=datetime(2024, 1, 20, 14, 45),
            body="""Dear Client,

We have completed our review of the contract dated January 18, 2024.

URGENT ITEMS REQUIRING ATTENTION:
1. Section 4.2 - Liability clause needs revision
2. Appendix B - Payment terms require clarification
3. Exhibit C - Intellectual property rights

Timeline:
- Review completed: January 20, 2024 at 2:45 PM
- Response required by: January 25, 2024
- Contract signing: January 30, 2024

Please contact us immediately at legal@lawfirm.com or (555) 987-6543.

Confidential Attorney-Client Communication
Case ID: CASE-2024-001
Document ID: DOC-20240120-001

Sincerely,
Attorney Name
Senior Partner
Law Firm LLP
"""
        )
        files.append(self._save_email(email2, "emails/legal_urgent.eml"))
        
        # Sample 3: Email thread with quoted replies
        email3 = self._create_email(
            from_addr="support@vendor.com",
            to_addr="admin@company.com",
            subject="RE: System Incident - Resolution Update",
            date=datetime(2024, 1, 22, 11, 15),
            body="""Hello,

The system incident has been resolved as of January 22, 2024 at 11:00 AM EST.

INCIDENT SUMMARY:
- Start time: January 21, 2024 at 3:30 PM EST
- End time: January 22, 2024 at 11:00 AM EST
- Duration: 19 hours 30 minutes
- Affected users: 1,247 accounts
- Root cause: Database connection timeout

RESOLUTION STEPS:
1. Identified connection pool exhaustion
2. Increased pool size from 50 to 200
3. Implemented connection retry logic
4. Applied database optimization patches

All services are now operational.

Best regards,
Technical Support Team
support@vendor.com

> -----Original Message-----
> From: admin@company.com
> Sent: Monday, January 21, 2024 4:15 PM
> To: support@vendor.com
> Subject: System Incident - Urgent
> 
> We are experiencing system outages affecting our operations.
> Please investigate immediately.
> 
> Incident started: January 21, 2024 at 3:30 PM
> Error messages: "Connection timeout"
> 
> Contact: admin@company.com
> Priority: CRITICAL
"""
        )
        files.append(self._save_email(email3, "emails/incident_resolution.eml"))
        
        return files
    
    def generate_document_samples(self) -> List[str]:
        """Generate various document samples"""
        files = []
        
        # Sample 1: Meeting notes
        meeting_notes = """# Project Kickoff Meeting Notes
Date: January 10, 2024
Time: 2:00 PM - 3:30 PM EST
Location: Conference Room A, New York Office
Attendees: John Doe, Jane Smith, Sarah Wilson, Mike Chen

## Agenda Items

### 1. Project Overview
- Project name: TimelineNarrator Development
- Start date: January 15, 2024
- Target completion: March 30, 2024
- Budget: $150,000

### 2. Team Assignments
- **John Doe** (Project Manager): Overall coordination
- **Jane Smith** (Technical Lead): Architecture design
- **Sarah Wilson** (Developer): Backend implementation
- **Mike Chen** (QA Engineer): Testing and validation

### 3. Key Milestones
| Milestone | Date | Owner |
|-----------|------|-------|
| Requirements finalization | Jan 20, 2024 | John Doe |
| Design approval | Feb 5, 2024 | Jane Smith |
| Alpha release | Feb 28, 2024 | Sarah Wilson |
| Beta testing | Mar 15, 2024 | Mike Chen |
| Production release | Mar 30, 2024 | Team |

### 4. Action Items
- [ ] John: Create project charter by Jan 12, 2024
- [ ] Jane: Complete technical specification by Jan 25, 2024
- [ ] Sarah: Set up development environment by Jan 18, 2024
- [ ] Mike: Prepare test strategy by Feb 1, 2024

## Next Meeting
Date: January 17, 2024
Time: 10:00 AM EST
Location: Virtual (Zoom)

Contact: john.doe@company.com for questions
"""
        files.append(self._save_text(meeting_notes, "documents/meeting_notes.md"))
        
        # Sample 2: Incident report
        incident_report = """INCIDENT REPORT
================

Report ID: INC-2024-001
Date: January 21, 2024
Time: 15:30 EST
Reporter: System Administrator
Status: RESOLVED

INCIDENT DETAILS
---------------
System: Production Database Server
Location: Data Center - Rack 12, Server DB-PROD-01
IP Address: 192.168.1.100

TIMELINE
--------
15:30 - Initial alert received (high CPU usage)
15:35 - Investigation started by admin@company.com
15:45 - Database connection issues identified
16:00 - Emergency response team activated
16:15 - Dr. Sarah Johnson (DBA) contacted at (555) 234-5678
17:30 - Temporary workaround implemented
23:45 - Root cause identified (memory leak in query optimizer)
11:00 (next day) - Permanent fix deployed

IMPACT ASSESSMENT
-----------------
Affected Users: 1,247 active sessions
Downtime: 19 hours 30 minutes
Revenue Impact: Estimated $45,000
Customer Complaints: 23 tickets filed

RESOLUTION
----------
1. Applied database patch v2.1.3
2. Increased memory allocation from 8GB to 16GB
3. Implemented query timeout limits
4. Added monitoring alerts for memory usage

PREVENTION MEASURES
------------------
- Weekly database health checks
- Automated memory monitoring
- Quarterly performance reviews
- Staff training on incident response

Report prepared by: admin@company.com
Reviewed by: Dr. Sarah Johnson (sarah.johnson@company.com)
Approved by: CTO Office (cto@company.com)

Document Classification: Internal Use Only
Created: 2024-01-22 09:00:00 EST
"""
        files.append(self._save_text(incident_report, "documents/incident_report.txt"))
        
        # Sample 3: CSV data
        csv_data = [
            ["Date", "Event", "Location", "Participants", "Notes"],
            ["2024-01-15", "Project Kickoff", "New York Office", "John Doe, Jane Smith", "Initial planning meeting"],
            ["2024-01-18", "Technical Review", "Virtual", "Jane Smith, Sarah Wilson", "Architecture discussion"],
            ["2024-01-21", "System Incident", "Data Center", "Admin Team", "Database outage - See INC-2024-001"],
            ["2024-01-22", "Incident Resolution", "Data Center", "Sarah Johnson, Mike Chen", "Applied fix and monitoring"],
            ["2024-01-25", "Status Update", "Conference Room B", "All Team", "Progress review and next steps"]
        ]
        csv_file = self.output_dir / "documents/project_timeline.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)
        files.append(str(csv_file))
        
        # Sample 4: JSON log data
        json_data = {
            "log_entries": [
                {
                    "timestamp": "2024-01-21T15:30:00Z",
                    "level": "ERROR",
                    "source": "database.connection",
                    "message": "Connection timeout after 30 seconds",
                    "user_id": "admin@company.com",
                    "session_id": "sess_abc123",
                    "ip_address": "192.168.1.50"
                },
                {
                    "timestamp": "2024-01-21T15:35:00Z",
                    "level": "WARN",
                    "source": "application.auth",
                    "message": "Multiple failed login attempts detected",
                    "user_id": "unknown",
                    "ip_address": "203.0.113.42",
                    "attempts": 5
                },
                {
                    "timestamp": "2024-01-21T16:00:00Z",
                    "level": "INFO",
                    "source": "incident.response",
                    "message": "Emergency response team activated",
                    "incident_id": "INC-2024-001",
                    "team_members": ["admin@company.com", "sarah.johnson@company.com"],
                    "priority": "CRITICAL"
                }
            ],
            "metadata": {
                "system": "TimelineNarrator",
                "version": "1.0.0",
                "generated": "2024-01-22T09:00:00Z",
                "total_entries": 3
            }
        }
        json_file = self.output_dir / "documents/system_logs.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2)
        files.append(str(json_file))
        
        return files
    
    def generate_pdf_samples(self) -> List[str]:
        """Generate PDF samples (placeholder - requires reportlab for full PDF generation)"""
        files = []
        
        # For now, create minimal PDF files that can be processed
        # In a full implementation, you'd use reportlab to create proper PDFs
        
        # Sample 1: Minimal PDF with text content
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Contract Agreement - January 2024) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000204 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
297
%%EOF"""
        
        pdf_file = self.output_dir / "pdfs/contract_agreement.pdf"
        with open(pdf_file, 'wb') as f:
            f.write(pdf_content)
        files.append(str(pdf_file))
        
        return files
    
    def generate_image_samples(self) -> List[str]:
        """Generate image samples with text content for OCR testing"""
        files = []
        
        # Sample 1: Document scan image
        img1 = Image.new('RGB', (800, 600), color='white')
        draw1 = ImageDraw.Draw(img1)
        
        # Try to use a basic font, fallback to default if not available
        try:
            font = ImageFont.truetype("arial.ttf", 24)
            small_font = ImageFont.truetype("arial.ttf", 16)
        except:
            try:
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            except:
                font = None
                small_font = None
        
        # Add text content that OCR can extract
        text_lines = [
            "CONFIDENTIAL DOCUMENT",
            "",
            "Meeting Minutes - January 15, 2024",
            "Time: 2:00 PM EST",
            "Location: Conference Room A",
            "",
            "Attendees:",
            "- John Doe (john.doe@company.com)",
            "- Jane Smith (jane.smith@company.com)", 
            "- Dr. Sarah Johnson (sarah.johnson@company.com)",
            "",
            "Agenda Items:",
            "1. Project status review",
            "2. Budget allocation discussion",
            "3. Timeline adjustments",
            "",
            "Key Decisions:",
            "- Approved additional $25,000 budget",
            "- Extended deadline to March 30, 2024",
            "- Added two new team members",
            "",
            "Action Items:",
            "- John: Update project plan by Jan 20",
            "- Jane: Review technical specifications",
            "- Sarah: Prepare database migration plan",
            "",
            "Next Meeting: January 22, 2024 at 10:00 AM",
            "Contact: john.doe@company.com",
            "",
            "Document ID: DOC-20240115-001",
            "Classification: Internal Use Only"
        ]
        
        y_position = 50
        for line in text_lines:
            if line.strip():
                if line.isupper() or "CONFIDENTIAL" in line:
                    current_font = font if font else small_font
                else:
                    current_font = small_font if small_font else font
                
                draw1.text((50, y_position), line, fill='black', font=current_font)
            y_position += 20
        
        img1_file = self.output_dir / "images/meeting_minutes_scan.jpg"
        img1.save(img1_file, 'JPEG', quality=95)
        files.append(str(img1_file))
        
        # Sample 2: Handwritten note image
        img2 = Image.new('RGB', (600, 800), color='#f8f8f8')
        draw2 = ImageDraw.Draw(img2)
        
        # Simulate handwritten text (printed text for OCR)
        handwritten_text = [
            "Personal Notes - Jan 21, 2024",
            "",
            "Phone call with Sarah Johnson",
            "Time: 4:30 PM",
            "Duration: 45 minutes",
            "",
            "Discussion points:",
            "- Database incident analysis",
            "- Recovery procedures", 
            "- Prevention strategies",
            "",
            "Key insights:",
            "- Memory leak in query optimizer",
            "- Need better monitoring",
            "- Team training required",
            "",
            "Follow-up actions:",
            "1. Schedule team meeting",
            "2. Review monitoring tools",
            "3. Update incident procedures",
            "",
            "Important dates:",
            "- Team meeting: Jan 25, 2024",
            "- Training session: Feb 1, 2024",
            "- Review deadline: Feb 15, 2024",
            "",
            "Contact info:",
            "Sarah: sarah.johnson@company.com",
            "Phone: (555) 234-5678",
            "",
            "Note ID: NOTE-20240121-001"
        ]
        
        y_pos = 40
        for line in handwritten_text:
            if line.strip():
                draw2.text((40, y_pos), line, fill='#333333', font=small_font)
            y_pos += 25
        
        img2_file = self.output_dir / "images/handwritten_notes.png"
        img2.save(img2_file, 'PNG')
        files.append(str(img2_file))
        
        return files
    
    def generate_pdf_samples(self) -> List[str]:
        """Generate more realistic PDF samples"""
        files = []
        
        # For testing purposes, create a more complex PDF structure
        # This would require reportlab for full implementation
        complex_pdf = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
/Metadata 5 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 200
>>
stream
BT
/F1 14 Tf
72 720 Td
(INVESTIGATION REPORT) Tj
0 -30 Td
(Date: January 20, 2024) Tj
0 -20 Td
(Case ID: CASE-2024-001) Tj
0 -30 Td
(Subject: System Security Incident) Tj
0 -30 Td
(Investigator: Dr. Sarah Johnson) Tj
0 -20 Td
(Email: sarah.johnson@company.com) Tj
0 -30 Td
(Timeline: Jan 21 15:30 - Jan 22 11:00) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Metadata
/Subtype /XML
/Length 150
>>
stream
<?xml version="1.0"?>
<metadata>
  <title>Investigation Report</title>
  <author>Dr. Sarah Johnson</author>
  <subject>System Security Incident</subject>
  <creator>TimelineNarrator</creator>
  <creation-date>2024-01-20T14:30:00Z</creation-date>
</metadata>
endstream
endobj

xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000068 00000 n 
0000000125 00000 n 
0000000214 00000 n 
0000000464 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
714
%%EOF"""
        
        pdf_file = self.output_dir / "pdfs/investigation_report.pdf"
        with open(pdf_file, 'wb') as f:
            f.write(complex_pdf)
        files.append(str(pdf_file))
        
        return files
    
    def _create_email(self, from_addr: str, to_addr: str, subject: str, 
                     date: datetime, body: str, cc_addr: str = None) -> MIMEMultipart:
        """Create an email message object"""
        msg = MIMEMultipart()
        msg['From'] = from_addr
        msg['To'] = to_addr
        if cc_addr:
            msg['Cc'] = cc_addr
        msg['Subject'] = subject
        msg['Date'] = date.strftime('%a, %d %b %Y %H:%M:%S %z')
        msg['Message-ID'] = f"<{uuid.uuid4()}@example.com>"
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        return msg
    
    def _save_email(self, email_msg: MIMEMultipart, filename: str) -> str:
        """Save email message to file"""
        file_path = self.output_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(email_msg.as_string())
        return str(file_path)
    
    def _save_text(self, content: str, filename: str) -> str:
        """Save text content to file"""
        file_path = self.output_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return str(file_path)
    
    def create_validation_dataset(self) -> Dict[str, Any]:
        """Create a validation dataset with expected extraction results"""
        return {
            "emails/business_update.eml": {
                "expected_entities": {
                    "people": ["John Doe", "Jane Smith", "Sarah Wilson", "Mike Chen"],
                    "organizations": ["Company Inc."],
                    "locations": ["New York"],
                    "emails": ["john.doe@company.com", "jane.smith@company.com"],
                    "dates": ["Jan 10, 2024", "Jan 12, 2024", "Jan 20, 2024"],
                    "phones": ["(555) 123-4567"]
                },
                "expected_datetime": datetime(2024, 1, 15, 9, 30),
                "expected_title": "Project Timeline Update",
                "expected_author": "john.doe@company.com"
            },
            "documents/meeting_notes.md": {
                "expected_entities": {
                    "people": ["John Doe", "Jane Smith", "Sarah Wilson", "Mike Chen"],
                    "dates": ["January 10, 2024", "January 15, 2024", "March 30, 2024"],
                    "locations": ["Conference Room A", "New York Office"],
                    "emails": ["john.doe@company.com"]
                },
                "expected_datetime": datetime(2024, 1, 10, 14, 0),
                "expected_title": "Project Kickoff Meeting Notes"
            },
            "images/meeting_minutes_scan.jpg": {
                "expected_entities": {
                    "people": ["John Doe", "Jane Smith", "Dr. Sarah Johnson"],
                    "emails": ["john.doe@company.com", "jane.smith@company.com", "sarah.johnson@company.com"],
                    "dates": ["January 15, 2024", "January 22, 2024"]
                },
                "expected_datetime": datetime(2024, 1, 15, 14, 0),
                "expected_title": "Meeting Minutes"
            }
        }

def main():
    """Generate all sample data"""
    generator = SampleDataGenerator()
    files = generator.generate_all_samples()
    
    print("\n📋 Generated Files:")
    for file_type, file_list in files.items():
        print(f"\n{file_type.upper()}:")
        for file_path in file_list:
            print(f"  ✓ {file_path}")
    
    # Create validation dataset
    validation_data = generator.create_validation_dataset()
    validation_file = generator.output_dir / "validation_dataset.json"
    with open(validation_file, 'w', encoding='utf-8') as f:
        json.dump(validation_data, f, indent=2, default=str)
    
    print(f"\n✅ Validation dataset saved to: {validation_file}")
    print(f"\n🎯 Total files created: {sum(len(v) for v in files.values())}")
    
    return files

if __name__ == "__main__":
    main()