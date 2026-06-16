export type ScopeType = 'Institucional' | 'Estatal/Regional' | 'Nacional' | 'Internacional';

export type ManagementType = 'Individualizada' | 'Colectiva';

export type ParticipationType = 'Interno' | 'Externo';

export type RoleType = 'Asistente' | 'Profesor/Instructor' | 'Asesor' | 'Presidente' | 'Responsable' | 'Participante' | 'Coautor' | 'Coordinador o Editor';

export type AcademicLevel = 'Licenciatura' | 'Maestría' | 'Doctorado' | 'Especialización Internacional';

export type ResourceProfile = 'Pedagógico' | 'Disciplinario';

export interface BaseActivity {
    id: string;
    year: number;
    hours: number;
    approved: boolean;
    institution: string;
    reportDate?: string; // Formato ISO 8601 YYYY-MM-DD
    submittedTo?: string;
    evidenceUrl?: string; // Mapeado desde el campo "PDF" del CV
    evaluationCode?: string; // Códigos de evaluación institucional (ej: "I.I.1", "I.IV.11")
}