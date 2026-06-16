import { AcademicLevel, ScopeType, ResourceProfile } from "./listed";

export interface AcademicDegree {
    id: string;
    level: AcademicLevel;
    title: string;              // Área/Disciplina o Título obtenido
    institution: string;
    startDate: number;
    endDate: number;
    graduationDate: string;     // YYYY-MM-DD
    thesisTitle?: string;
    professionalId?: string;    // "En trámite" o número de cédula
    degreeStatus: 'Finalizado' | 'En trámite';
}

export interface Certification {
    id: string;
    title: string;              // Nombre del Diplomado
    institution: string;
    profile: ResourceProfile;
    scope: ScopeType;
    startDate: string;
    endDate: string;
    hours: number;
    year: number;
    credits?: number;
}