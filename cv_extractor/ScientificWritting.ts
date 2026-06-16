import { ScopeType } from "./listed";

export type AcademicProduction =
    | JournalArticle
    | Book
    | BookChapter
    | DigitalResource
    | ConferencePresentation;

export interface BaseProduction {
    id: string;
    authors: string[];
    title: string;
    year: number;
    purpose: 'Investigación' | 'Docencia' | 'Difusión';
    evaluationCode?: string;
}

export interface JournalArticle extends BaseProduction {
    type: 'Artículo Científico';
    journalName: string;
    volume: number;
    number: string;
    startPage: number;
    endPage: number;
    issn: string;
    isPeerReviewed: boolean;
    impactFactor?: number;
    doiOrUrl?: string;
    countryOrLocation: string;
}

export interface Book extends BaseProduction {
    type: 'Libro';
    role: 'Coautor' | 'Coordinador o Editor';
    editorial: string;
    isbn: string;
    pages: number;
    editionNumber: number;
    circulation: 'Impreso' | 'online' | string;
    country: string;
    ebookUrl?: string;
}

export interface BookChapter extends BaseProduction {
    type: 'Capítulo de Libro';
    bookTitle: string;
    chapterTitle: string;
    editorial: string;
    isbn?: string;
    startPage: number;
    endPage: number;
    editionNumber: number;
    country: string;
}

export interface DigitalResource extends BaseProduction {
    type: 'Material Didáctico' | 'Práctica Innovadora';
    resourceType: 'Recurso digital' | 'Digitales';
    description: string;
    accessUrl?: string;
}

export interface ConferencePresentation extends BaseProduction {
    type: 'Ponencia/Conferencia';
    eventName: string;
    presentationType: 'Externo' | 'Libro' | 'Invitación';
    modality: 'Presencial' | 'Virtual';
    location: string;
    country: string;
    date: string; // YYYY-MM-DD
    scope: ScopeType;
}