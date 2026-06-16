#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CV scraper (enhanced) – extracts all structured data from a Mexican academic CV PDF.
Uses layout-aware word extraction to handle multiple columns and tables cleanly.
"""

import re
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pdfplumber


# ---------- Helper functions ----------
def clean_text(text: str) -> str:
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def safe_int(value_str: str, default: int = 0) -> int:
    if not value_str:
        return default
    clean = re.sub(r'[^0-9]', '', value_str.strip())
    try:
        return int(clean) if clean else default
    except ValueError:
        return default


def safe_float(value_str: str, default: Optional[float] = None) -> Optional[float]:
    if not value_str:
        return default
    clean = re.sub(r'[^0-9.]', '', value_str.strip())
    if clean.count('.') > 1:
        parts = clean.split('.')
        clean = parts[0] + '.' + ''.join(parts[1:])
    try:
        return float(clean)
    except ValueError:
        return default


def fix_latin1_encoding(text: str) -> str:
    if not text:
        return ""
    try:
        return text.encode('latin-1').decode('utf-8')
    except:
        replacements = {
            "Ã¡": "á", "Ã©": "é", "Ã­": "í", "Ã³": "ó", "Ãº": "ú",
            "Ã±": "ñ", "Ã ": "Á", "Ã‰": "É", "Ã ": "Í", "Ã“": "Ó",
            "Ãš": "Ú", "Ã‘": "Ñ", "Â": ""
        }
        for bad, good in replacements.items():
            text = text.replace(bad, good)
        return text


def extract_owner_name_from_filename(pdf_path: str) -> str:
    name = Path(pdf_path).stem
    name = re.sub(r'^CV\d*_?', '', name)
    return name


# ---------- Layout-Aware Text Extraction ----------
def extract_layout_aware_lines(pdf_path: str) -> List[str]:
    all_lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words()
            # Group words by vertical 'top' coordinate within tolerance
            lines_dict = {}
            for w in words:
                top = w['top']
                found = False
                for t in lines_dict:
                    if abs(t - top) < 3.0:
                        lines_dict[t].append(w)
                        found = True
                        break
                if not found:
                    lines_dict[top] = [w]
            
            # Sort the lines by vertical position
            sorted_tops = sorted(lines_dict.keys())
            for t in sorted_tops:
                line_words = sorted(lines_dict[t], key=lambda w: w['x0'])
                
                left_col = []
                right_col = []
                for w in line_words:
                    if w['x0'] < 280:
                        left_col.append(w['text'])
                    else:
                        right_col.append(w['text'])
                
                left_str = " ".join(left_col).strip()
                right_str = " ".join(right_col).strip()
                
                if left_str or right_str:
                    all_lines.append(f"{left_str}\t{right_str}")
    return all_lines


def clean_layout_lines(raw_lines: List[str]) -> List[str]:
    cleaned = []
    for line in raw_lines:
        parts = line.split("\t")
        left = parts[0].strip()
        right = parts[1].strip() if len(parts) > 1 else ""
        
        combined = f"{left} {right}".strip()
        if not combined:
            continue
        if combined == "Sistema Institucional de Curriculum Vitae":
            continue
        if combined in ("Curriculum vitae", "Curriculum"):
            continue
        if re.search(r"Página\s+\d+/\d+", combined, re.IGNORECASE):
            continue
        if re.match(r"^CV\d+.*", combined):
            continue
            
        cleaned.append(line)
    return cleaned


def split_into_sections(lines: List[str]) -> Dict[str, List[str]]:
    sections = {
        "PERSONAL": [],
        "DATOS_LABORALES": [],
        "FORMACION_ACADEMICA": [],
        "PARTICIPACIONES": [],
        "PRODUCCION": [],
        "RECURSOS_HUMANOS": [],
        "GESTION_ACADEMICA": []
    }
    
    current_section = "PERSONAL"
    
    for line in lines:
        plain_line = line.replace("\t", " ").strip()
        
        if plain_line == "DATOS LABORALES":
            current_section = "DATOS_LABORALES"
            continue
        elif plain_line == "FORMACIÓN ACADÉMICA":
            current_section = "FORMACION_ACADEMICA"
            continue
        elif plain_line in ("PARTICIPACIÓNES ACADÉMICAS", "PARTICIPACIONES ACADÉMICAS"):
            current_section = "PARTICIPACIONES"
            continue
        elif plain_line == "PRODUCCIÓN ACADÉMICA CIENTÍFICA":
            current_section = "PRODUCCION"
            continue
        elif plain_line == "FORMACIÓN DE RECURSOS HUMANOS":
            current_section = "RECURSOS_HUMANOS"
            continue
        elif plain_line == "GESTIÓN ACADÉMICA":
            current_section = "GESTION_ACADEMICA"
            continue
            
        sections[current_section].append(line)
        
    return sections


# ---------- Section Parsers ----------
def parse_personal_and_labor(personal_lines: List[str], labor_lines: List[str]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    p_left = []
    p_right = []
    for line in personal_lines:
        parts = line.split("\t")
        p_left.append(parts[0].strip())
        if len(parts) > 1:
            p_right.append(parts[1].strip())
            
    p_left_text = "\n".join([x for x in p_left if x])
    p_right_text = "\n".join([x for x in p_right if x])
    p_combined = p_left_text + "\n" + p_right_text
    
    # Contact Info
    institutional_email = ""
    additional_email = None
    phone = ""
    native_language = "Español"
    home_address = None
    
    m_info = re.search(r"Correo institucional Lengua materna Teléfono\s*\n\s*(\S+)\s+(\S+)\s+(\S+)", p_combined, re.IGNORECASE)
    if m_info:
        institutional_email = m_info.group(1).strip()
        native_language = m_info.group(2).strip()
        phone = m_info.group(3).strip()
    else:
        m_email = re.search(r"([a-zA-Z0-9._%+-]+@ucol\.mx)", p_combined)
        if m_email:
            institutional_email = m_email.group(1)
        m_phone = re.search(r"\b(\d{10})\b", p_combined)
        if m_phone:
            phone = m_phone.group(1)
            
    m_add_email = re.search(r"Correo adicional\s*\n\s*(\S+)", p_combined, re.IGNORECASE)
    if m_add_email:
        additional_email = m_add_email.group(1).strip()
        
    m_address = re.search(r"Domicilio particular\s*\n\s*(.*)", p_combined, re.IGNORECASE)
    if m_address:
        home_address = m_address.group(1).strip()
        
    contact_info = {
        "institutionalEmail": institutional_email,
        "additionalEmail": additional_email,
        "phone": phone,
        "nativeLanguage": native_language,
        "homeAddress": home_address
    }
    
    # Employee Number
    employee_number = 0
    m_emp = re.search(r"No\.\s+de\s+trabajador:\s*(\d+)", p_combined, re.IGNORECASE)
    if m_emp:
        employee_number = int(m_emp.group(1))
        
    # Labor Data
    l_left = []
    l_right = []
    for line in labor_lines:
        parts = line.split("\t")
        l_left.append(parts[0].strip())
        if len(parts) > 1:
            l_right.append(parts[1].strip())
            
    l_left_text = "\n".join([x for x in l_left if x])
    l_right_text = "\n".join([x for x in l_right if x])
    
    current_appointment = ""
    admission_date = ""
    academic_unit = ""
    work_address = ""
    body_code = ""
    body_name = ""
    consolidation_level = "CAEC"
    
    m_appoint = re.search(r"Nombramiento actual\s*\n\s*(.*?)\s+(\d{4}-\d{2}-\d{2})", l_left_text + "\n" + l_right_text, re.IGNORECASE)
    if m_appoint:
        current_appointment = m_appoint.group(1).strip()
        admission_date = m_appoint.group(2).strip()
        
    m_unit = re.search(r"DES\s+Unidad académica\s*\n\s*(.*)", l_left_text + "\n" + l_right_text, re.IGNORECASE)
    if m_unit:
        unit_str = m_unit.group(1).strip()
        parts = [p.strip() for p in unit_str.split("  ") if p.strip()]
        if parts:
            academic_unit = parts[0]
            
    m_work_addr = re.search(r"Domicilio laboral\s*\n\s*(.*?)\s*(?:Evaluar|$)", l_left_text + "\n" + l_right_text, re.DOTALL | re.IGNORECASE)
    if m_work_addr:
        work_address = m_work_addr.group(1).replace("\n", " ").strip()
        
    m_body = re.search(r"(UCOL-CA-\d+)\s*-\s*(.*)", l_left_text + "\n" + l_right_text)
    if m_body:
        body_code = m_body.group(1).strip()
        body_name = m_body.group(2).strip()
        body_name = re.sub(r"\b(CAEC|CA-En-Consolidación|CA-Consolidado)\b.*", "", body_name).strip()
        
    if "CAEC" in l_left_text or "CAEC" in l_right_text:
        consolidation_level = "CAEC"
    elif "En-Consolid" in l_left_text or "En-Consolid" in l_right_text:
        consolidation_level = "CA-En-Consolidación"
    elif "Consolidado" in l_left_text or "Consolidado" in l_right_text:
        consolidation_level = "CA-Consolidado"
        
    labor_data = {
        "employeeNumber": employee_number,
        "currentAppointment": fix_latin1_encoding(current_appointment),
        "admissionDate": admission_date,
        "academicUnit": fix_latin1_encoding(academic_unit),
        "workAddress": fix_latin1_encoding(work_address),
        "academicBody": {
            "code": body_code,
            "name": fix_latin1_encoding(body_name),
            "consolidationLevel": consolidation_level
        }
    }
    
    return contact_info, labor_data


def parse_academic_formation(lines: List[str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    subsections = {
        "ESTUDIOS": [],
        "DIPLOMADOS": [],
        "OTROS": []
    }
    current_sub = "ESTUDIOS"
    for line in lines:
        plain = line.replace("\t", " ").strip()
        if plain == "Estudios realizados":
            current_sub = "ESTUDIOS"
            continue
        elif plain == "Diplomados":
            current_sub = "DIPLOMADOS"
            continue
        elif plain == "Otros":
            current_sub = "OTROS"
            continue
        subsections[current_sub].append(line)
        
    # Studies Blocks
    study_blocks = []
    current_block = []
    for line in subsections["ESTUDIOS"]:
        plain = line.replace("\t", " ").strip()
        if plain.startswith("...."):
            if current_block:
                study_blocks.append(current_block)
                current_block = []
        else:
            current_block.append(line)
    if current_block:
        study_blocks.append(current_block)
        
    # Diplomados Blocks
    diplomado_blocks = []
    current_block = []
    for line in subsections["DIPLOMADOS"]:
        plain = line.replace("\t", " ").strip()
        if plain.startswith("...."):
            if current_block:
                diplomado_blocks.append(current_block)
                current_block = []
        else:
            current_block.append(line)
    if current_block:
        diplomado_blocks.append(current_block)
        
    degrees = parse_academic_degree_blocks(study_blocks)
    certs = parse_certification_blocks(diplomado_blocks)
    
    return degrees, certs


def parse_academic_degree_blocks(blocks: List[List[str]]) -> List[Dict[str, Any]]:
    degrees = []
    for idx, block_lines in enumerate(blocks):
        left_parts = []
        right_parts = []
        for line in block_lines:
            parts = line.split("\t")
            left_parts.append(parts[0].strip())
            if len(parts) > 1:
                right_parts.append(parts[1].strip())
                
        left_text = "\n".join([p for p in left_parts if p])
        right_text = "\n".join([p for p in right_parts if p])
        combined_text = left_text + "\n" + right_text
        
        level = "Licenciatura"
        for lvl in ["Doctorado", "Maestría", "Licenciatura", "Especialización Internacional"]:
            if lvl in combined_text:
                level = lvl
                break
                
        start_date = 0
        end_date = 0
        years = []
        for line in block_lines:
            found = re.findall(r"\b(19\d{2}|20\d{2})\b", line)
            if len(found) >= 2:
                years = [int(y) for y in found[:2]]
                break
        if not years:
            found = re.findall(r"\b(19\d{2}|20\d{2})\b", combined_text)
            if len(found) >= 2:
                years = [int(found[0]), int(found[1])]
        if years:
            start_date, end_date = years[0], years[1]
            
        graduation_date = ""
        m_grad = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", combined_text)
        if m_grad:
            graduation_date = m_grad.group(1)
            
        evaluation_code = None
        m_eval = re.search(r"Evaluar en:\s*([\w.]+)", combined_text)
        if m_eval:
            evaluation_code = m_eval.group(1)
            
        title = ""
        institution = ""
        professional_id = None
        thesis_title = None
        
        if "Licenciatura" in left_text and "Área" in right_text:
            for i, line in enumerate(left_parts):
                if "Licenciatura" in line:
                    if i + 1 < len(left_parts):
                        title = left_parts[i+1].strip()
                    break
            for i, line in enumerate(left_parts):
                if "Institución" in line:
                    if i + 1 < len(left_parts):
                        institution = left_parts[i+1].strip()
                        right_line = right_parts[i+1].strip() if i+1 < len(right_parts) else ""
                        if right_line.isdigit():
                            professional_id = right_line
                    break
            m_thesis = re.search(r"Tema de proyecto\s*\n\s*(.*)", left_text + "\n" + right_text, re.IGNORECASE)
            if m_thesis:
                thesis_line = m_thesis.group(1).strip()
                thesis_line = re.sub(r"\b\d{4}-\d{2}-\d{2}\b.*", "", thesis_line)
                thesis_line = re.sub(r"Evaluar en:.*", "", thesis_line)
                thesis_title = thesis_line.strip()
        else:
            for i, line in enumerate(left_parts):
                if "Nivel de estudios" in line:
                    if i + 1 < len(left_parts):
                        institution = right_parts[i+1].strip() if i+1 < len(right_parts) else ""
                    break
            for i, line in enumerate(left_parts):
                if "Área" in line and "Disciplina" in line:
                    if i + 1 < len(left_parts):
                        r_line = right_parts[i+1].strip() if i+1 < len(right_parts) else ""
                        for area in ["Ingeniería y tecnología", "Educación, Humanidades y Arte", "Educación, Humanidades y Artes"]:
                            if r_line.startswith(area):
                                r_line = r_line[len(area):].strip()
                                break
                        parts = r_line.split()
                        if parts:
                            if "En trámite" in r_line or "En tramite" in r_line:
                                professional_id = "En trámite"
                                title = r_line.replace("En trámite", "").replace("En tramite", "").strip()
                            elif parts[-1].isdigit():
                                professional_id = parts[-1]
                                title = " ".join(parts[:-1]).strip()
                            else:
                                title = r_line
                    break
            m_thesis = re.search(r"Título de la tesis\s*\n\s*(.*)", left_text + "\n" + right_text, re.DOTALL | re.IGNORECASE)
            if m_thesis:
                thesis_content = m_thesis.group(1).strip()
                thesis_content = re.sub(r"Fecha de inicio.*", "", thesis_content, flags=re.DOTALL | re.IGNORECASE)
                thesis_content = re.sub(r"Evaluar en:.*", "", thesis_content, flags=re.DOTALL | re.IGNORECASE)
                lines_th = [l.strip() for l in thesis_content.split("\n")]
                filtered_lines = [l for l in lines_th if l.lower() != "tesis" and l]
                thesis_title = " ".join(filtered_lines).strip()
                thesis_title = re.sub(r"\s+", " ", thesis_title)
                
        degree_status = "En trámite" if professional_id == "En trámite" else "Finalizado"
        
        degrees.append({
            "id": f"deg_{idx+1}",
            "level": level,
            "title": fix_latin1_encoding(title),
            "institution": fix_latin1_encoding(institution),
            "startDate": start_date,
            "endDate": end_date,
            "graduationDate": graduation_date,
            "thesisTitle": fix_latin1_encoding(thesis_title) if thesis_title else None,
            "professionalId": professional_id if professional_id and professional_id != "En trámite" else None,
            "degreeStatus": degree_status,
            "evaluationCode": evaluation_code
        })
    return degrees


def extract_title_and_institution_cert(left_parts: List[str], right_parts: List[str]) -> Tuple[str, str]:
    content_lines = []
    for i, line in enumerate(left_parts):
        if "Perfil" in line and "Alcance" in line:
            break
        if "Diplomado" in line and "Institución" in line:
            continue
        content_lines.append(line.strip())
        if i < len(right_parts):
            content_lines.append(right_parts[i].strip())
            
    content_lines = [l for l in content_lines if l]
    
    known_insts = [
        "Universidad de Colima",
        "CENTRO UNIVERSITARIO MAR DE CORTÉS",
        "Centro Universitario CIFE",
        "Anáhuac",
        "Instituto Tecnológico de Colima",
        "Universidad de Granada"
    ]
    
    institution = ""
    title_parts = []
    
    for line in content_lines:
        found_inst = False
        for inst in known_insts:
            if inst.lower() in line.lower():
                institution = inst
                m_rest = re.sub(re.escape(inst), "", line, flags=re.IGNORECASE).strip()
                if m_rest:
                    title_parts.append(m_rest)
                found_inst = True
                break
        if not found_inst:
            title_parts.append(line)
            
    title = " ".join(title_parts).strip()
    title = re.sub(r"\s+", " ", title)
    return title, institution


def parse_certification_blocks(blocks: List[List[str]]) -> List[Dict[str, Any]]:
    certs = []
    for idx, block_lines in enumerate(blocks):
        left_parts = []
        right_parts = []
        for line in block_lines:
            parts = line.split("\t")
            left_parts.append(parts[0].strip())
            if len(parts) > 1:
                right_parts.append(parts[1].strip())
                
        left_text = "\n".join([p for p in left_parts if p])
        right_text = "\n".join([p for p in right_parts if p])
        combined_text = left_text + "\n" + right_text
        
        title, institution = extract_title_and_institution_cert(left_parts, right_parts)
        
        profile = "Pedagógico"
        scope = "Institucional"
        start_date = ""
        end_date = ""
        hours = 0
        year = 0
        credits_val = None
        evaluation_code = None
        
        for i, line in enumerate(left_parts):
            if "Perfil" in line and "Alcance" in line:
                if i + 1 < len(left_parts):
                    p_val = left_parts[i+1].strip()
                    r_val = right_parts[i+1].strip() if i+1 < len(right_parts) else ""
                    
                    if "Pedagógico" in p_val:
                        profile = "Pedagógico"
                    elif "Disciplinario" in p_val:
                        profile = "Disciplinario"
                        
                    if "Internacional" in p_val:
                        scope = "Internacional"
                    elif "Nacional" in p_val:
                        scope = "Nacional"
                    elif "Estatal/Regional" in p_val or "Estatal" in p_val or "Regional" in p_val:
                        scope = "Estatal/Regional"
                    else:
                        scope = "Institucional"
                        
                    period = r_val
                    period_parts = re.split(r'\s+al\s+|\s+-\s+', period)
                    if len(period_parts) >= 2:
                        start_date = period_parts[0].strip()
                        end_date = period_parts[1].strip()
                    else:
                        start_date = period
                break
                
        for i, line in enumerate(left_parts):
            if "Horas" in line and "Año" in line:
                if i + 1 < len(left_parts):
                    l_val = left_parts[i+1].strip()
                    r_val = right_parts[i+1].strip() if i+1 < len(right_parts) else ""
                    
                    parts = l_val.split()
                    if len(parts) >= 2:
                        hours = safe_int(parts[0])
                        year = safe_int(parts[1])
                    if r_val:
                        credits_val = safe_float(r_val)
                break
                
        m_eval = re.search(r"Evaluar en:\s*([\w.]+)", combined_text)
        if m_eval:
            evaluation_code = m_eval.group(1)
            
        certs.append({
            "id": f"cert_{idx+1}",
            "title": fix_latin1_encoding(title),
            "institution": fix_latin1_encoding(institution),
            "profile": profile,
            "scope": scope,
            "startDate": start_date,
            "endDate": end_date,
            "hours": hours,
            "year": year,
            "credits": credits_val,
            "evaluationCode": evaluation_code
        })
    return certs


def parse_academic_participations_section(lines: List[str]) -> List[Dict[str, Any]]:
    blocks = []
    current_block = []
    for line in lines:
        plain = line.replace("\t", " ").strip()
        if plain.startswith("...."):
            if current_block:
                blocks.append(current_block)
                current_block = []
        else:
            current_block.append(line)
    if current_block:
        blocks.append(current_block)
        
    participations = []
    for idx, block_lines in enumerate(blocks):
        left_parts = []
        right_parts = []
        for line in block_lines:
            parts = line.split("\t")
            left_parts.append(parts[0].strip())
            if len(parts) > 1:
                right_parts.append(parts[1].strip())
                
        left_text = "\n".join([p for p in left_parts if p])
        right_text = "\n".join([p for p in right_parts if p])
        combined_text = left_text + "\n" + right_text
        
        event_type = ""
        institution = ""
        event_name = ""
        profile = "Pedagógico"
        role = ""
        hours = 0
        year = 0
        scope = None
        evaluation_code = None
        
        for i, line in enumerate(left_parts):
            if "Tipo" in line and "Institución" in line:
                if i + 1 < len(left_parts):
                    tipo_str = left_parts[i+1].strip()
                    inst_str = right_parts[i+1].strip() if i+1 < len(right_parts) else ""
                    event_type = tipo_str
                    institution = inst_str
                break
                
        event_name_parts = []
        started = False
        for i, line in enumerate(left_parts):
            if "Nombre del evento" in line:
                started = True
                continue
            if "Perfil" in line and "Participación" in line:
                started = False
                break
            if started:
                event_name_parts.append(line)
        event_name = " ".join([x for x in event_name_parts if x]).strip()
        event_name = re.sub(r"\s+", " ", event_name)
        
        for i, line in enumerate(left_parts):
            if "Perfil" in line and "Participación" in line:
                if i + 1 < len(left_parts):
                    l_val = left_parts[i+1].strip()
                    r_val = right_parts[i+1].strip() if i+1 < len(right_parts) else ""
                    
                    if "Pedagógico" in l_val:
                        profile = "Pedagógico"
                    elif "Disciplinario" in l_val:
                        profile = "Disciplinario"
                        
                    role_hours = l_val.replace(profile, "").strip()
                    m_role = re.match(r"(.*?)(?:\s*)(\d+)$", role_hours)
                    if m_role:
                        role = m_role.group(1).strip()
                        hours = safe_int(m_role.group(2))
                    else:
                        role = role_hours
                        hours = 0
                        
                    r_parts = r_val.split()
                    if r_parts:
                        year = safe_int(r_parts[0])
                break
                
        m_scope = re.search(r"Alcance\s+(.*?)(?:\s+Evaluar|$)", combined_text, re.IGNORECASE)
        if m_scope:
            scope = m_scope.group(1).strip()
            
        m_eval = re.search(r"Evaluar en:\s*([\w.]+)", combined_text)
        if m_eval:
            evaluation_code = m_eval.group(1)
            
        participations.append({
            "id": f"part_{idx+1}",
            "year": year,
            "hours": hours,
            "approved": True,
            "institution": fix_latin1_encoding(institution),
            "eventName": fix_latin1_encoding(event_name),
            "profile": profile,
            "role": role,
            "eventType": event_type,
            "scope": scope,
            "evaluationCode": evaluation_code
        })
    return participations


# ---------- Production Helper ----------
def get_field(field_name: str, block: str) -> str:
    pattern = rf"{re.escape(field_name)}:\s*(.*?)(?=(?:\s+\w+(?:\([\w\)]+\))?:\s+)|$)"
    m = re.search(pattern, block, re.DOTALL)
    if m:
        return m.group(1).strip().rstrip('.')
    return ""


def parse_academic_productions(production_section_text: str) -> List[Dict[str, Any]]:
    blocks = production_section_text.split("Producción:")
    productions = []
    
    for idx, block in enumerate(blocks):
        block = block.strip()
        if not block:
            continue
            
        first_dot = block.find(".")
        if first_dot == -1:
            continue
        block_type = block[:first_dot].strip()
        
        authors_str = get_field("Autor(es)", block)
        if authors_str.startswith("Coordinadores:"):
            authors_str = authors_str[len("Coordinadores:"):].strip()
        authors = [a.strip() for a in re.split(r'[;,]', authors_str) if a.strip()]
        
        year = safe_int(get_field("Año", block))
        purpose = get_field("Propósito", block)
        eval_code = get_field("Evaluar en", block)
        
        prod_id = f"prod_{idx+1}"
        
        if "Artículo científico" in block_type:
            title = get_field("Título del artículo", block)
            journal = get_field("Revista", block)
            if " (" in journal:
                journal = journal.split(" (")[0].strip()
                
            date_str = get_field("Fecha", block)
            if not year and date_str:
                year = safe_int(date_str[:4])
                
            if not purpose:
                purpose = "Investigación"
                
            productions.append({
                "id": prod_id,
                "type": "Artículo Científico",
                "authors": [fix_latin1_encoding(a) for a in authors],
                "title": fix_latin1_encoding(title),
                "year": year,
                "purpose": purpose,
                "journalName": fix_latin1_encoding(journal),
                "volume": safe_int(get_field("Volumen", block)),
                "number": get_field("Número", block),
                "startPage": safe_int(get_field("Página de inicio", block)),
                "endPage": safe_int(get_field("Página final", block)),
                "issn": get_field("ISNN", block) or get_field("ISSN", block),
                "isPeerReviewed": get_field("Arbitrado", block) == "1",
                "impactFactor": safe_float(get_field("Factor de Impacto (FI)", block)),
                "doiOrUrl": get_field("Dirección electrónica", block),
                "countryOrLocation": fix_latin1_encoding(get_field("Lugar de edición", block)),
                "evaluationCode": eval_code if eval_code else None
            })
            
        elif "Libro" in block_type:
            title = get_field("Título", block)
            if not purpose:
                purpose = "Difusión"
            role = get_field("Colaboración", block)
            if not role:
                role = "Coautor"
                
            productions.append({
                "id": prod_id,
                "type": "Libro",
                "authors": [fix_latin1_encoding(a) for a in authors],
                "title": fix_latin1_encoding(title),
                "year": year,
                "purpose": purpose,
                "role": role,
                "editorial": fix_latin1_encoding(get_field("Editorial", block)),
                "isbn": get_field("ISBN", block),
                "pages": safe_int(get_field("Páginas", block)),
                "editionNumber": safe_int(get_field("No. de edición", block)) or 1,
                "circulation": get_field("Tiraje", block),
                "country": fix_latin1_encoding(get_field("País de edición", block)),
                "ebookUrl": get_field("Enlace e-book", block),
                "evaluationCode": eval_code if eval_code else None
            })
            
        elif "Capítulo de libro" in block_type:
            title = get_field("Título del capítulo del libro", block)
            if not purpose:
                purpose = "Investigación"
                
            productions.append({
                "id": prod_id,
                "type": "Capítulo de Libro",
                "authors": [fix_latin1_encoding(a) for a in authors],
                "title": fix_latin1_encoding(title),
                "year": year,
                "purpose": purpose,
                "bookTitle": fix_latin1_encoding(get_field("Título del libro", block)),
                "chapterTitle": fix_latin1_encoding(title),
                "editorial": fix_latin1_encoding(get_field("Editorial", block)),
                "isbn": get_field("ISBN", block),
                "startPage": safe_int(get_field("Página de inicio", block)),
                "endPage": safe_int(get_field("Página final", block)),
                "editionNumber": safe_int(get_field("No. de edición", block)) or 1,
                "country": fix_latin1_encoding(get_field("País de edición", block)),
                "evaluationCode": eval_code if eval_code else None
            })
            
        elif "Material didáctico" in block_type or "Prácticas educativas innovadoras" in block_type:
            desc = get_field("Descripción", block) or get_field("Descripción de la práctica", block)
            if "Material didáctico" in block_type:
                title = get_field("Título", block)
                res_type = get_field("Material", block) or "Recurso digital"
                prod_type = "Material Didáctico"
            else:
                title = desc[:50] + "..." if len(desc) > 50 else desc
                res_type = get_field("Tipo", block) or "Digitales"
                prod_type = "Práctica Innovadora"
                
            if not purpose:
                purpose = "Docencia"
                
            productions.append({
                "id": prod_id,
                "type": prod_type,
                "authors": [fix_latin1_encoding(a) for a in authors],
                "title": fix_latin1_encoding(title),
                "year": year,
                "purpose": purpose,
                "resourceType": res_type,
                "description": fix_latin1_encoding(desc),
                "accessUrl": get_field("Enlace", block) or get_field("Enlace externo para descarga", block),
                "evaluationCode": eval_code if eval_code else None
            })
            
        elif "Ponencias y conferencias" in block_type:
            title = get_field("Título de la ponencia o conferencia", block)
            event = get_field("Evento donde se presentó", block)
            date_str = get_field("Fecha", block)
            if not year and date_str:
                year = safe_int(date_str[:4])
            if not purpose:
                purpose = "Difusión"
                
            productions.append({
                "id": prod_id,
                "type": "Ponencia/Conferencia",
                "authors": [fix_latin1_encoding(a) for a in authors],
                "title": fix_latin1_encoding(title),
                "year": year,
                "purpose": purpose,
                "eventName": fix_latin1_encoding(event),
                "presentationType": get_field("Tipo", block) or "Externo",
                "modality": get_field("Modalidad", block) or "Presencial",
                "location": fix_latin1_encoding(get_field("Lugar", block)),
                "country": fix_latin1_encoding(get_field("País", block)),
                "date": date_str,
                "scope": get_field("Alcance", block),
                "evaluationCode": eval_code if eval_code else None
            })
            
        else:
            title = get_field("Título", block) or f"{block_type} {idx+1}"
            if not purpose:
                purpose = "Investigación"
            productions.append({
                "id": prod_id,
                "type": block_type,
                "authors": [fix_latin1_encoding(a) for a in authors],
                "title": fix_latin1_encoding(title),
                "year": year,
                "purpose": purpose,
                "description": fix_latin1_encoding(get_field("Descripción", block)),
                "evaluationCode": eval_code if eval_code else None
            })
            
    return productions


# ---------- Resources Humanos Parsers ----------
def parse_teaching_blocks(blocks: List[List[str]]) -> List[Dict[str, Any]]:
    courses = []
    for idx, block_lines in enumerate(blocks):
        left_parts = []
        right_parts = []
        for line in block_lines:
            parts = line.split("\t")
            left_parts.append(parts[0].strip())
            if len(parts) > 1:
                right_parts.append(parts[1].strip())
                
        left_text = "\n".join([p for p in left_parts if p])
        right_text = "\n".join([p for p in right_parts if p])
        combined_text = left_text + "\n" + right_text
        
        faculty = "Facultad de Ingeniería Mecánica y Eléctrica"
        
        course_name_parts = []
        for line in left_parts:
            if "Curso impartido" in line:
                continue
            if "Programa educativo" in line:
                break
            course_name_parts.append(line)
            
        course_name_raw = " ".join([x for x in course_name_parts if x]).strip()
        temp = course_name_raw
        segments = [
            "Facultad de Ingeniería Mecánica y Eléctrica",
            "Facultad de IngenierÃa Mecánica y Eléctrica",
            "Facultad de Ingeniería Mecánica",
            "Facultad de IngenierÃa",
            "Mecánica y Eléctrica",
            "y Eléctrica"
        ]
        for seg in segments:
            temp = temp.replace(seg, "")
        course_name = re.sub(r"\s+", " ", temp).strip()
        
        program = ""
        for i, line in enumerate(left_parts):
            if "Programa educativo" in line:
                if i + 1 < len(left_parts):
                    program = left_parts[i+1].strip()
                    if "Inteligente" in combined_text and "Inteligente" not in program:
                        program += " Inteligente"
                break
                
        level = "Licenciatura"
        if "Maestría" in combined_text or "Maestria" in combined_text:
            level = "Maestría"
        elif "Doctorado" in combined_text:
            level = "Doctorado"
            
        is_accredited = False
        m_acred = re.search(r"Acreditado\s*(Sí|No|Si)", combined_text, re.IGNORECASE)
        if m_acred:
            is_accredited = m_acred.group(1).lower() in ["sí", "si"]
            
        weekly_hours = 0
        m_hours = re.search(r"Carga horaria semanal\s*(\d+)", combined_text)
        if m_hours:
            weekly_hours = int(m_hours.group(1))
            
        semester_group = ""
        student_count = 0
        period = ""
        year = 0
        
        m_vals = re.search(r"Semestre y\s+group\(s\)\s+No\.\s+de\s+alumnos\s+Periodo\s+escolar\s+Año\s+(.*?)(?:\s+Evaluar|$)", combined_text, re.IGNORECASE)
        if m_vals:
            val_line = m_vals.group(1).strip()
            parts = val_line.split()
            if len(parts) >= 4:
                year = safe_int(parts[-1])
                period = parts[-2]
                student_count = safe_int(parts[-3])
                semester_group = " ".join(parts[:-3])
        else:
            for i, line in enumerate(left_parts):
                if "Semestre y" in line:
                    if i + 1 < len(left_parts):
                        val_line = left_parts[i+1].strip()
                        parts = val_line.split()
                        if len(parts) >= 3:
                            semester_group = parts[0]
                            student_count = safe_int(parts[1])
                            period = parts[2]
                        if i+1 < len(right_parts) and right_parts[i+1]:
                            year = safe_int(right_parts[i+1])
                    break
                    
        evaluation_code = None
        m_eval = re.search(r"Evaluar en:\s*([\w.]+)", combined_text)
        if m_eval:
            evaluation_code = m_eval.group(1)
            
        courses.append({
            "courseName": fix_latin1_encoding(course_name),
            "faculty": fix_latin1_encoding(faculty),
            "program": fix_latin1_encoding(program),
            "level": level,
            "semesterGroup": semester_group,
            "studentCount": student_count,
            "period": period,
            "year": year,
            "weeklyHours": weekly_hours,
            "isAccredited": is_accredited,
            "evaluationCode": evaluation_code
        })
    return courses


def parse_thesis_blocks(blocks: List[List[str]]) -> List[Dict[str, Any]]:
    theses = []
    for idx, block_lines in enumerate(blocks):
        left_parts = []
        right_parts = []
        for line in block_lines:
            parts = line.split("\t")
            left_parts.append(parts[0].strip())
            if len(parts) > 1:
                right_parts.append(parts[1].strip())
                
        left_text = "\n".join([p for p in left_parts if p])
        right_text = "\n".join([p for p in right_parts if p])
        combined_text = left_text + "\n" + right_text
        
        student_name = ""
        m_student = re.search(r"Nombre del estudiante\n(.*?)\n(?:Plantel|$)", left_text, re.DOTALL)
        if m_student:
            student_name = m_student.group(1).replace("\n", " ").strip()
            
        institution = ""
        m_inst = re.search(r"Plantel\n(.*?)\n(?:Programa educativo|$)", left_text, re.DOTALL)
        if m_inst:
            institution = m_inst.group(1).replace("\n", " ").strip()
            
        program = ""
        m_prog = re.search(r"Programa educativo\n(.*?)\n(?:Fecha de término|$)", left_text, re.DOTALL)
        if m_prog:
            program = m_prog.group(1).replace("\n", " ").strip()
            
        end_date = ""
        m_date = re.search(r"Fecha de término\n(.*?)$", left_text, re.DOTALL)
        if m_date:
            end_date = m_date.group(1).replace("\n", " ").strip()
            end_date = re.search(r"^\d{4}-\d{2}-\d{2}", end_date).group(0) if re.search(r"^\d{4}-\d{2}-\d{2}", end_date) else end_date
            
        thesis_title = ""
        m_title = re.search(r"Título de la tesis\n(.*?)\n(?:Nivel académico|$)", right_text, re.DOTALL)
        if m_title:
            thesis_title = m_title.group(1).replace("\n", " ").strip()
            
        direction_type = ""
        m_dir = re.search(r"Tipo de dirección\n(.*?)\n(?:Fecha del examen|examen|$)", right_text, re.DOTALL)
        if m_dir:
            direction_type = m_dir.group(1).replace("\n", " ").strip()
            
        evaluation_code = None
        m_eval = re.search(r"Evaluar en:\s*([\w.]+)", combined_text)
        if m_eval:
            evaluation_code = m_eval.group(1)
            
        theses.append({
            "studentName": fix_latin1_encoding(student_name),
            "thesisTitle": fix_latin1_encoding(thesis_title),
            "institution": fix_latin1_encoding(institution),
            "program": fix_latin1_encoding(program),
            "directionType": fix_latin1_encoding(direction_type),
            "endDate": end_date,
            "evaluationCode": evaluation_code
        })
    return theses


def parse_resources_humanos(lines: List[str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    subsections = {
        "DOCENCIA": [],
        "TESIS": []
    }
    current_sub = "DOCENCIA"
    for line in lines:
        plain = line.replace("\t", " ").strip()
        if plain == "Docencia":
            current_sub = "DOCENCIA"
            continue
        elif plain == "Tesis o proyectos":
            current_sub = "TESIS"
            continue
        subsections[current_sub].append(line)
        
    doc_blocks = []
    current_block = []
    for line in subsections["DOCENCIA"]:
        plain = line.replace("\t", " ").strip()
        if plain.startswith("...."):
            if current_block:
                doc_blocks.append(current_block)
                current_block = []
        else:
            current_block.append(line)
    if current_block:
        doc_blocks.append(current_block)
        
    thesis_blocks = []
    current_block = []
    for line in subsections["TESIS"]:
        plain = line.replace("\t", " ").strip()
        if plain.startswith("...."):
            if current_block:
                thesis_blocks.append(current_block)
                current_block = []
        else:
            current_block.append(line)
    if current_block:
        thesis_blocks.append(current_block)
        
    courses = parse_teaching_blocks(doc_blocks)
    theses = parse_thesis_blocks(thesis_blocks)
    
    return courses, theses


# ---------- Academic Management Parsers ----------
def parse_management_section(lines: List[str]) -> List[Dict[str, Any]]:
    blocks = []
    current_block = []
    for line in lines:
        plain = line.replace("\t", " ").strip()
        if plain.startswith("...."):
            if current_block:
                blocks.append(current_block)
                current_block = []
        else:
            current_block.append(line)
    if current_block:
        blocks.append(current_block)
        
    activities = []
    for idx, block_lines in enumerate(blocks):
        left_parts = []
        right_parts = []
        for line in block_lines:
            parts = line.split("\t")
            left_parts.append(parts[0].strip())
            if len(parts) > 1:
                right_parts.append(parts[1].strip())
                
        left_text = "\n".join([p for p in left_parts if p])
        right_text = "\n".join([p for p in right_parts if p])
        combined_text = left_text + "\n" + right_text
        
        mgmt_type = ""
        participation_type = ""
        level = "Participante"
        commission = ""
        scope = ""
        cargo = ""
        function = ""
        last_report_date = ""
        approved = False
        weekly_hours = 0
        status = ""
        evaluation_code = None
        
        for i, line in enumerate(left_parts):
            if "Tipo de gestión" in line and "Tipo de participación" in line:
                if i + 1 < len(left_parts):
                    mgmt_type = left_parts[i+1].strip()
                    r_val = right_parts[i+1].strip() if i+1 < len(right_parts) else ""
                    r_parts = r_val.split()
                    if len(r_parts) >= 2:
                        participation_type = r_parts[0]
                        level = r_parts[1]
                    elif len(r_parts) == 1:
                        participation_type = r_parts[0]
                break
                
        m_comm = re.search(r"Comisión o actividad\n(.*?)\n(?:Alcance|$)", left_text, re.DOTALL)
        if m_comm:
            commission = m_comm.group(1).replace("\n", " ").strip()
            
        for i, line in enumerate(left_parts):
            if "Alcance" in line and "Cargo" in line:
                if i + 1 < len(left_parts):
                    scope = left_parts[i+1].strip()
                    cargo = right_parts[i+1].strip() if i+1 < len(right_parts) else ""
                break
                
        m_func = re.search(r"Función encomendada\n(.*?)\n(?:Fecha|$)", left_text, re.DOTALL)
        if m_func:
            function = m_func.group(1).replace("\n", " ").strip()
            
        m_date = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", left_text)
        if m_date:
            last_report_date = m_date.group(1)
            
        m_appr = re.search(r"\b(Sí|No|Si)\b", right_text, re.IGNORECASE)
        if m_appr:
            approved = m_appr.group(1).lower() in ["sí", "si"]
            
        m_hours = re.search(r"dedicadas\n(\d+)", left_text, re.IGNORECASE)
        if m_hours:
            weekly_hours = int(m_hours.group(1))
            
        m_status = re.search(r"Estado\n(Concluido|En curso)", right_text, re.IGNORECASE)
        if m_status:
            status = m_status.group(1).strip()
            
        m_eval = re.search(r"Evaluar en:\s*([\w.]+)", combined_text)
        if m_eval:
            evaluation_code = m_eval.group(1)
            
        activities.append({
            "type": mgmt_type,
            "participationType": participation_type,
            "level": level,
            "commission": fix_latin1_encoding(commission),
            "scope": scope,
            "function": fix_latin1_encoding(function),
            "lastReportDate": last_report_date,
            "approved": approved,
            "weeklyHours": weekly_hours,
            "status": status,
            "evaluationCode": evaluation_code
        })
    return activities


# ---------- Main scraping entrypoint ----------
def scrape_cv_to_single_json(pdf_path: str, output_dir: str = "cv_output") -> str:
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Extract layout-aware lines
    raw_lines = extract_layout_aware_lines(pdf_path)
    cleaned_lines = clean_layout_lines(raw_lines)
    
    # Split into sections
    sections = split_into_sections(cleaned_lines)
    
    # Parse contact and labor details
    contact_info, labor_data = parse_personal_and_labor(sections["PERSONAL"], sections["DATOS_LABORALES"])
    
    # Parse academic degrees and certifications
    degrees, certs = parse_academic_formation(sections["FORMACION_ACADEMICA"])
    
    # Parse academic participations
    participations = parse_academic_participations_section(sections["PARTICIPACIONES"])
    
    # Parse academic productions
    prod_section_text = "\n".join(sections["PRODUCCION"])
    productions = parse_academic_productions(prod_section_text)
    
    # Parse teaching and theses
    courses, theses = parse_resources_humanos(sections["RECURSOS_HUMANOS"])
    
    # Parse academic management activities
    management = parse_management_section(sections["GESTION_ACADEMICA"])
    
    owner_name = extract_owner_name_from_filename(pdf_path)
    
    data = {
        "ownerName": owner_name,
        "contactInfo": contact_info,
        "laborData": labor_data,
        "academicDegrees": degrees,
        "certifications": certs,
        "academicParticipations": participations,
        "teachingCourses": courses,
        "thesisDirections": theses,
        "managementActivities": management,
        "academicProductions": productions
    }
    
    json_path = output_path / f"{owner_name}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    print(f"✅ Saved CV data to {json_path}")
    return str(json_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scrapping.py <pdf_file1> [pdf_file2 ...]")
        sys.exit(1)
    for pdf_file in sys.argv[1:]:
        if not Path(pdf_file).exists():
            print(f"❌ File not found: {pdf_file}")
            continue
        try:
            scrape_cv_to_single_json(pdf_file)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ Error processing {pdf_file}: {e}")