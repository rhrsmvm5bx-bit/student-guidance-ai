import pymupdf
import os
import json

doc = pymupdf.open("lecture.pdf")
all_image_metadata = []  # List to store metadata for all images
all_text_metadata = []  # List to store metadata for all text blocks
print("Total pages:", doc.page_count)

def calculate_box_distance(bbox1, bbox2):
    dx=max(0,bbox1[0]-bbox2[2],bbox2[0]-bbox1[2])
    dy=max(0,bbox1[1]-bbox2[3],bbox2[1]-bbox1[3])
    return (dx**2 + dy**2)**0.5

def calculate_center_distance(bbox1, bbox2):
    center1 = ((bbox1[0] + bbox1[2]) / 2, (bbox1[1] + bbox1[3]) / 2)
    center2 = ((bbox2[0] + bbox2[2]) / 2, (bbox2[1] + bbox2[3]) / 2)
    return ((center1[0] - center2[0]) ** 2 + (center1[1] - center2[1]) ** 2) ** 0.5

def find_nearest_text(image,all_text_metadata):
    data=[]
    for text in all_text_metadata:
        if text["page_number"] == image["page_number"]:
            distance = calculate_box_distance(image["bbox"], text["bbox"])
            data.append (
            {
                "text": text["text"],
                "distance": distance
            }
            )
    sorted_data=sorted(data, key=lambda item: item["distance"])
    return sorted_data[:5] 
            

with open("lecture.txt", "w") as file:
    for page in doc:
        file.write(f"Page {page.number + 1}:\n")
        data = page.get_text("dict")
        img_counter = 1  # Initialize image counter for each page
        for block in data["blocks"]:
            if block["type"] == 0:  # Only process text blocks
                for line in block["lines"]:
                    line_text = " ".join(
                        span["text"] for span in line["spans"] if span["text"].strip() != ""
                        )
                    if line_text :
                        file.write(line_text + "\n")
                        print(line_text + "\n")
                        line_metadata = {
                            "text": line_text,
                            "page_number": page.number + 1,
                            "bbox": list(line["bbox"])  # Convert bbox to a list for JSON serialization
                        }
                        all_text_metadata.append(line_metadata)

            elif block["type"] == 1:  # Process image blocks
                # note=f"Image block found on page {page.number + 1}, bbox={block['bbox']}"
                # file.write(note + "\n")
                # print(note + "\n")
                image = block["image"]
                ext = block["ext"]
                os.makedirs("extracted_images", exist_ok=True)
                file_name = f"page_{page.number + 1}_img_{img_counter}.{ext}"
                img_path = os.path.join("extracted_images", file_name)
                img_counter += 1  # Increment image counter for each image
                with open(img_path, "wb") as img_file:
                    img_file.write(image)
                bbox = list(block["bbox"])  # Convert bbox to a list for JSON serialization
                image_metadata = {
                    "file_name": file_name,
                    "page_number": page.number + 1,
                    "bbox": bbox
                }
                all_image_metadata.append(image_metadata)
doc.close()

with open("image_metadata.json", "w") as metadata_file:
    json.dump(all_image_metadata, metadata_file , indent=4)

with open("text_metadata.json", "w") as metadata_file:
    json.dump(all_text_metadata, metadata_file, indent=4)

with open("nearest_texts.json", "w") as nearest_texts_file:
    nearest_texts_list = []
    for image in all_image_metadata:
        nearest_texts = find_nearest_text(image, all_text_metadata)
        nearest_texts_list.append(
            {
                "image_file_name": image["file_name"],
                "page_number": image["page_number"],
                "nearest_texts": nearest_texts
            }
        )
    json.dump(nearest_texts_list, nearest_texts_file, indent=4)