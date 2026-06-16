
export interface ContactInfo {
    fullName: string;
    institutionalEmail: string; // ej: wmata@ucol.mx
    additionalEmail?: string;   // ej: waltermata@gmail.com
    phone: string;
    nativeLanguage: string;
    homeAddress?: string;
}

export interface AcademicBody {
    code: string;               // ej: "UCOL-CA-91"
    name: string;               // ej: "AUTOMATIZACIÓN Y SISTEMAS EMBEBIDOS"
    consolidationLevel: 'CAEC' | 'CA-En-Consolidación' | 'CA-Consolidado';
}

export interface LaborData {
    employeeNumber: number;
    currentAppointment: string; // ej: "Profesor investigador de tiempo completo"
    admissionDate: string;      // YYYY-MM-DD
    academicUnit: string;       // ej: "Facultad de Ingeniería Mecánica y Eléctrica"
    workAddress: string;
    academicBody: AcademicBody;
}