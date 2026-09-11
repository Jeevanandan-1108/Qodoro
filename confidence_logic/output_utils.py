import os
import json
import shutil

SUCCESS_DIR = "EOB_output_success"
FAILED_DIR  = "EOB_output_failed"

def split_patients_by_validation(final):
    """
    Supports both validation structures:

    1. EOB/page-level validation:
       {
           "patients": [...],
           "validation": {
               "status": True/False,
               "errors": [...]
           }
       }

    2. Patient-level validation:
       {
           "patients": [
               {
                   ...,
                   "validation": {
                       "status": True/False,
                       "errors": [...]
                   }
           ]
       }
    """

    success_final = []
    failed_final = []

    for eob in final:

        # -------------------------------------------------
        # CASE 1: EOB/page-level validation
        # -------------------------------------------------
        if "validation" in eob:

            validation = eob.get("validation") or {}
            status = validation.get("status")

            if status is True:
                success_final.append(eob)
            else:
                failed_final.append(eob)

        # -------------------------------------------------
        # CASE 2: Patient-level validation
        # -------------------------------------------------
        else:

            patients = eob.get("patients", [])

            success_patients = []
            failed_patients = []

            for patient in patients:

                validation = patient.get("validation") or {}
                status = validation.get("status")

                if status is True:
                    success_patients.append(patient)
                else:
                    failed_patients.append(patient)

            if success_patients:
                success_final.append({
                    **eob,
                    "patients": success_patients
                })

            if failed_patients:
                failed_final.append({
                    **eob,
                    "patients": failed_patients
                })

    return success_final, failed_final




def _copy_pdf_and_crops(pdf_path, cropped_dir, dest_dir):
    """
    Copies the source PDF and the entire cropped_images folder
    into dest_dir/<pdf_basename>/
    """
    os.makedirs(dest_dir, exist_ok=True)

    # copy PDF
    if pdf_path and os.path.exists(pdf_path):
        pdf_dest = os.path.join(dest_dir, os.path.basename(pdf_path))
        shutil.copy2(pdf_path, pdf_dest)

    # copy cropped images folder
    if cropped_dir and os.path.isdir(cropped_dir):
        crops_dest = os.path.join(dest_dir, "cropped_images")
        # copytree needs the dest to not already exist (py<3.8) —
        # dirs_exist_ok=True handles reruns safely on py>=3.8
        shutil.copytree(cropped_dir, crops_dest, dirs_exist_ok=True)


def save_split_output(final, company_name, pdf_name, pdf_path=None, cropped_dir=None):
    """
    Saves validated patients + source PDF + crops to:
        EOB_output_success/<company>/<pdf_name>/{pdf_name}_output.json, <pdf>.pdf, cropped_images/

    Saves failed patients + source PDF + crops to:
        EOB_output_failed/<company>/<pdf_name>/{pdf_name}_output.json, <pdf>.pdf, cropped_images/

    If a PDF has both success and failed patients, BOTH folders get
    a full copy of the PDF and crops (so each folder is self-contained).

    Returns (success_path, failed_path) — json paths, either can be None.
    """
    success_final, failed_final = split_patients_by_validation(final)

    success_path = None
    failed_path = None

    if success_final:
        success_case_dir = os.path.join(SUCCESS_DIR, company_name, pdf_name)
        os.makedirs(success_case_dir, exist_ok=True)

        success_path = os.path.join(success_case_dir, f"{pdf_name}_output.json")
        with open(success_path, "w", encoding="utf-8") as f:
            json.dump(success_final, f, indent=2, ensure_ascii=False)

        _copy_pdf_and_crops(pdf_path, cropped_dir, success_case_dir)
        print(f"✅ Success output + pdf + crops saved: {success_case_dir}")

    if failed_final:
        failed_case_dir = os.path.join(FAILED_DIR, company_name, pdf_name)
        os.makedirs(failed_case_dir, exist_ok=True)

        failed_path = os.path.join(failed_case_dir, f"{pdf_name}_output.json")
        with open(failed_path, "w", encoding="utf-8") as f:
            json.dump(failed_final, f, indent=2, ensure_ascii=False)

        _copy_pdf_and_crops(pdf_path, cropped_dir, failed_case_dir)
        print(f"⚠ Failed output + pdf + crops saved: {failed_case_dir}")

    return success_path, failed_path