// services/api.ts
import type { PlanType } from "./api.type";
import type { ConfigItems } from "../store/config.type";
import type {Field} from '../components/forms/dynamicform.type'

export class ApiService {
  private baseUrl: string;

  constructor() {
    const isDevelopment = process.env.NODE_ENV === 'development';
    this.baseUrl = isDevelopment 
      ? 'http://localhost:8000/api/v1'
      : '/api/v1';
  }

  private getFullUrl(endpoint: string): string {
    return `${this.baseUrl}${endpoint}`;
  }

  private async request<T>(endpoint: string, options: RequestInit): Promise<T> {
    try {
      const response = await fetch(this.getFullUrl(endpoint), {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...(options.headers || {}),
        }
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const contentType = response.headers.get('content-type');
      return contentType && contentType.includes('application/json')
        ? await response.json()
        : ({} as T);  // ou throw si tu attends toujours du JSON
    } catch (error) {
      console.error('API error:', error);
      throw error;
    }
  }

  // Exemple de méthode métier
  async sendPlans(plans: PlanType[]): Promise<boolean> {
    return this.request<boolean>('/observation/plans', {
      method: 'POST',
      body: JSON.stringify(plans),
    });
  }

  async sendConfig(config : ConfigItems) {
    return this.request<boolean>('/config', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getConfig() {
    return this.request<ConfigItems>('/config', {
      method: 'GET'
    });
  }

  async getConfigScheme(): Promise<Field[]> {
    return this.request<Field[]>('/config/scheme', {
      method: 'GET'
    });
  }

  
  async getObservatory() : Promise<ConfigItems[]> {
    return this.request<ConfigItems[]>('/config/observatory', {
      method: 'GET'
    });
  }

  async setObservatory(observatoryConfiguration : ConfigItems[]) : Promise<void> {
    this.request<ConfigItems[]>('/config/observatory', {
      method: 'POST',
      body: JSON.stringify(observatoryConfiguration)
    });
  }

  async getObservatoryScheme(): Promise<Field[]> {
    return this.request<Field[]>('/config/observatory/schema', {
      method: 'GET'
    });
  }

  // Exemple pour un GET générique
  async getSomething<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'GET',
    });
  }
}

// Instance globale
export const apiService = new ApiService();
