import pymupdf  # PyMuPDF
import os

class DataParser:
    def __init__(self):
        pass

    def pdf_to_markdown(self, pdf_path, output_md, images_dir):
        doc = pymupdf.open(pdf_path)
        os.makedirs(images_dir, exist_ok=True)
        md_lines = []
        img_count = 0
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text = page.get_text("text")  # plain text; for structured output: use 'dict' or 'blocks'
            # Add page heading
            md_lines.append(f"\n## Page {page_num + 1}\n")
            md_lines.append(text.strip())
            # Extract images
            images = page.get_images(full=True)
            for img_index, img in enumerate(images):
                xref = img[0]
                pix = pymupdf.Pixmap(doc, xref)
                if pix.n < 5:
                    img_path = os.path.join(images_dir, f"page{page_num+1}_img{img_index+1}.png")
                    pix.save(img_path)
                else:
                    pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                    img_path = os.path.join(images_dir, f"page{page_num+1}_img{img_index+1}.png")
                    pix.save(img_path)
                pix = None
                md_lines.append(f"\n![Image {page_num+1}-{img_index+1}]({img_path})\n")
                img_count += 1

        with open(output_md, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))

        print(f"Markdown created at {output_md} with {img_count} images.")

    def process_folder(self, folder_path, output_dir):
        for filename in os.listdir(folder_path):
            if filename.endswith('.pdf'):
                pdf_path = os.path.join(folder_path, filename)
                output_md = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}.md")
                images_dir = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}_images")
                self.pdf_to_markdown(pdf_path, output_md, images_dir)

    def process_xlsx(self, xlsx_path, output_dir):
        print(f"Processing XLSX file: {xlsx_path}")

parser = DataParser()
parser.process_folder("./dataset/pdf_files", "./dataset/markdown_files")
parser.process_xlsx("./dataset/schedule.xlsx", "./dataset/markdown_files")
