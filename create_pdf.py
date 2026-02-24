#!/usr/bin/env python3
"""
Convert HTML to PDF using various methods
"""
import subprocess
import sys
import os

html_file = "/Users/ksr1939/interview/devops_interview_guide.html"
pdf_file = "/Users/ksr1939/interview/devops_interview_guide.pdf"

def try_weasyprint():
    """Try using weasyprint"""
    try:
        import weasyprint
        print("Using WeasyPrint...")
        weasyprint.HTML(filename=html_file).write_pdf(pdf_file)
        return True
    except ImportError:
        print("WeasyPrint not available")
        return False
    except Exception as e:
        print(f"WeasyPrint error: {e}")
        return False

def try_pdfkit():
    """Try using pdfkit (wkhtmltopdf wrapper)"""
    try:
        import pdfkit
        print("Using pdfkit...")
        pdfkit.from_file(html_file, pdf_file)
        return True
    except ImportError:
        print("pdfkit not available")
        return False
    except Exception as e:
        print(f"pdfkit error: {e}")
        return False

def install_and_try_weasyprint():
    """Install weasyprint and try again"""
    print("Attempting to install WeasyPrint...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "weasyprint"])
        return try_weasyprint()
    except Exception as e:
        print(f"Could not install WeasyPrint: {e}")
        return False

if __name__ == "__main__":
    print("Attempting to convert HTML to PDF...")
    print(f"Input: {html_file}")
    print(f"Output: {pdf_file}")
    print()

    # Try methods in order
    if try_weasyprint():
        print(f"✅ Success! PDF created at: {pdf_file}")
        sys.exit(0)

    if try_pdfkit():
        print(f"✅ Success! PDF created at: {pdf_file}")
        sys.exit(0)

    # Try installing weasyprint
    if install_and_try_weasyprint():
        print(f"✅ Success! PDF created at: {pdf_file}")
        sys.exit(0)

    # If all methods fail, provide instructions
    print("\n❌ Could not create PDF automatically.")
    print("\n📝 You have two options:")
    print(f"\n1. Open the HTML file in your browser and print to PDF:")
    print(f"   open {html_file}")
    print(f"   Then: File → Print → Save as PDF")
    print(f"\n2. Install WeasyPrint manually:")
    print(f"   pip3 install weasyprint")
    print(f"   python3 {__file__}")
    print(f"\n3. Use pandoc with LaTeX (requires BasicTeX):")
    print(f"   # Install BasicTeX first (will require your password):")
    print(f"   brew install --cask basictex")
    print(f"   eval \"$(/usr/libexec/path_helper)\"")
    print(f"   pandoc devops_interview_guide.md -o devops_interview_guide.pdf")

    sys.exit(1)
