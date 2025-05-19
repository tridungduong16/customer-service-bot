import fitz  # PyMuPDF
import os

def pdf_to_markdown(pdf_path, output_md, images_dir):
    doc = fitz.open(pdf_path)
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
            pix = fitz.Pixmap(doc, xref)
            if pix.n < 5:  # this is GRAY or RGB
                img_path = os.path.join(images_dir, f"page{page_num+1}_img{img_index+1}.png")
                pix.save(img_path)
            else:  # CMYK: convert to RGB first
                pix = fitz.Pixmap(fitz.csRGB, pix)
                img_path = os.path.join(images_dir, f"page{page_num+1}_img{img_index+1}.png")
                pix.save(img_path)
            pix = None  # cleanup

            md_lines.append(f"\n![Image {page_num+1}-{img_index+1}]({img_path})\n")
            img_count += 1

    # Write to Markdown file
    with open(output_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"Markdown created at {output_md} with {img_count} images.")

pdf_to_markdown("input.pdf", "output.md", "images")
