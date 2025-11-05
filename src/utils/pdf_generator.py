"""
PDF Generator utility for creating combined PDFs
"""
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PIL import Image
import io

def create_combined_pdf(activation_id, user_data, documents_data, output_dir="uploads/combined_pdfs"):
    """
    Create a combined PDF with user data and documents
    
    Args:
        activation_id: ID of the activation
        user_data: Dictionary with user information
        documents_data: Dictionary with document file paths
        output_dir: Directory to save the PDF
    
    Returns:
        str: Path to the generated PDF file
    """
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate PDF filename
        pdf_filename = f"activation_{activation_id}_combined.pdf"
        pdf_path = os.path.join(output_dir, pdf_filename)
        
        # Create PDF
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        
        # Add title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, f"Ativação #{activation_id}")
        
        # Add user information
        c.setFont("Helvetica", 12)
        y_position = height - 100
        
        if user_data:
            c.drawString(50, y_position, f"Nome: {user_data.get('name', 'N/A')}")
            y_position -= 20
            c.drawString(50, y_position, f"CPF: {user_data.get('cpf', 'N/A')}")
            y_position -= 20
            c.drawString(50, y_position, f"Email: {user_data.get('email', 'N/A')}")
            y_position -= 40
        
        # Add document images if available
        if documents_data:
            for doc_type, doc_path in documents_data.items():
                if doc_path and os.path.exists(doc_path):
                    try:
                        # Add new page for each document
                        c.showPage()
                        c.setFont("Helvetica-Bold", 14)
                        c.drawString(50, height - 50, f"Documento: {doc_type}")
                        
                        # Add image
                        img = Image.open(doc_path)
                        img_width, img_height = img.size
                        
                        # Scale image to fit page
                        max_width = width - 100
                        max_height = height - 150
                        
                        scale = min(max_width / img_width, max_height / img_height)
                        new_width = img_width * scale
                        new_height = img_height * scale
                        
                        c.drawImage(doc_path, 50, height - 100 - new_height, 
                                  width=new_width, height=new_height)
                    except Exception as e:
                        print(f"Error adding image {doc_path}: {e}")
                        c.drawString(50, height - 100, f"Erro ao carregar imagem: {doc_type}")
        
        c.save()
        return pdf_path
        
    except Exception as e:
        print(f"Error creating combined PDF: {e}")
        return None