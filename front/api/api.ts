// services/api.ts
import type { PlanType, DarkLibraryType, DarkLibraryProcessType, PlansHistory, ImageSettings, FhwmType, FwhmResults} from "../types/api.type";
import type { ConfigItems } from "../store/config.type";
import type {Field} from '../types/dynamicform.type'

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

  getBaseUrl():string {
    return this.baseUrl
  }

  // Exemple de méthode métier
  async sendPlans(plans: PlanType[]): Promise<boolean> {
    return this.request<boolean>('/observation/start', {
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
    return this.request<ConfigItems[]>('/observatories', {
      method: 'GET'
    });
  }

  async setObservatory(observatoryConfiguration : ConfigItems[]) : Promise<void> {
    this.request<ConfigItems[]>('/observatories', {
      method: 'POST',
      body: JSON.stringify(observatoryConfiguration)
    });
  }


  async setCurrentObservatory(observatory : string) : Promise<void> {
      this.request<ConfigItems[]>('/observatories/current', {
        method: 'PUT',
        body: JSON.stringify({observatory})
      });
  }

  async getObservatoryScheme(): Promise<Field[]> {
    return this.request<Field[]>('/observatories/schema', {
      method: 'GET'
    });
  }

  async getCurrentObservatory(): Promise<ConfigItems> {
    return this.request<ConfigItems>('/observatories/current', {
      method: 'GET'
    });
  }

  async getTelescope(): Promise<ConfigItems[]> {
    return this.request<ConfigItems[]>('/telescopes', {
      method: 'GET'
    });
  }

  async getTelescopeSchema(): Promise<Field[]> {
    return this.request<Field[]>('/telescopes/schema', {
      method: 'GET'
    });


  }
  async setTelescope(telescopeConfiguration : ConfigItems[]) : Promise<void> {
    this.request<ConfigItems[]>('/telescopes', {
      method: 'POST',
      body: JSON.stringify(telescopeConfiguration)
    });
  }


  async getCurrentTelescope(): Promise<ConfigItems> {
    return this.request<ConfigItems>('/telescopes/current', {
      method: 'GET'
    });
  }


  async setCurrentTelescope(telescope: string): Promise<void> {
    this.request<ConfigItems>('/telescopes/current', {
      method: 'PUT',
      body: JSON.stringify({telescope})
    });

  }


  async getImageSettings(): Promise<ImageSettings> {
    return this.request<ImageSettings>('/observation/image_settings', {
      method: 'GET',
    });
  }

    async setImageSettings(stretch:number, black_point: number): Promise<void> {
    this.request<ConfigItems>('/observation/image_settings', {
      method: 'PUT',
      body: JSON.stringify({stretch, black_point})
    });

  }

  async getCameras(): Promise<ConfigItems[]> {
    return this.request<ConfigItems[]>('/cameras', {
      method: 'GET'
    });
  }

  async getCamerasSchema(): Promise<Field[]> {
    return this.request<Field[]>('/cameras/schema', {
      method: 'GET'
    });


  }
  async setCameras(telescopeConfiguration : ConfigItems[]) : Promise<void> {
    this.request<ConfigItems[]>('/cameras', {
      method: 'POST',
      body: JSON.stringify(telescopeConfiguration)
    });
  }


  async getCurrentCamera(): Promise<ConfigItems> {
    return this.request<ConfigItems>('/cameras/current', {
      method: 'GET'
    });
  }


  async setCurrentCamera(camera: string): Promise<void> {
    this.request<ConfigItems>('/cameras/current', {
      method: 'PUT',
      body: JSON.stringify({camera})
    });

  }


  
  async getFilterWheels(): Promise<ConfigItems[]> {
    return this.request<ConfigItems[]>('/filterwheels', {
      method: 'GET'
    });
  }

  async getFilterWheelsSchema(): Promise<Field[]> {
    return this.request<Field[]>('/filterwheels/schema', {
      method: 'GET'
    });


  }
  async setFilterWheels(wheelConfiguration : ConfigItems[]) : Promise<void> {
    this.request<ConfigItems[]>('/filterwheels', {
      method: 'POST',
      body: JSON.stringify(wheelConfiguration)
    });
  }


  async getCurrentFilterWheel(): Promise<ConfigItems> {
    return this.request<ConfigItems>('/filterwheels/current', {
      method: 'GET'
    });
  }


  async setCurrentFilterWheel(wheel: string): Promise<void> {
    this.request<ConfigItems>('/filterwheels/current', {
      method: 'PUT',
      body: JSON.stringify({wheel})
    });

  }

  async getIsPlanRunning(): Promise<boolean> {
    return this.request<boolean>('/observation/is_running', {
      method: 'GET',
    });
  }


  async stopPlan(): Promise<boolean> {
    return this.request<boolean>('/observation/stop', {
      method: 'POST',
       body: ''
    });
  }


  async getPlanHistory(): Promise<PlansHistory> {
    return this.request<PlansHistory>(`/observation/history`, {
      method: 'GET',
    });
  }

  async getDarkForCamera(camera: string): Promise<DarkLibraryType[]> {
    return this.request<DarkLibraryType[]>(`/dark/${camera}`, {
      method: 'GET',
    });
  }

    async stopDarkProcessing(): Promise<boolean> {
    return this.request<boolean>(`/dark/stop`, {
      method: 'POST',

    });
  }

  async deleteDark(camera:string, id: string) : Promise<DarkLibraryProcessType[]> {
      return this.request<DarkLibraryProcessType[]>(`/dark/${camera}/${id}`, {
        method: 'DELETE',
      });
  }

  async setNewDarkForCamera(camera: string, newDark:DarkLibraryType[]): Promise<boolean> {

    return this.request<boolean>(`/dark/${camera}`, {
      method: 'PUT',
      body: JSON.stringify(newDark)
    });
  }


    async getDarkProcessing(): Promise<DarkLibraryProcessType[]> {
      return this.request<DarkLibraryProcessType[]>("/dark/current_process", {
        method: 'GET',
      });
  }

  async getIsConnected(): Promise<Record<string, boolean>> {
    return this.request<Record<string, boolean>>('/status/is_connected', {
      method: 'GET',
    });
  }

  async getHardwareName(): Promise<Record<string, string>> {
    return this.request<Record<string, string>>('/status/connected_hardware', {
      method: 'GET',
    });
  }

  async connectHardWare(): Promise<Record<string, boolean>> {
    return this.request<Record<string, boolean>>('/status/connect_hardware', {
      method: 'POST',
    });
  }

  async setUtcDate(date: string): Promise<Record<string, string>> {
    return this.request<Record<string, string>>('/status/set_telescope_date', {
      method: 'POST',
      body: JSON.stringify({date})
    });
  }


  async getMaxFocuser(): Promise<number> {
    return this.request<number>('/focuser/max', {
      method: 'GET',
    });
  }

  
  async getFocuserPosition(): Promise<number> {
    return this.request<number>('/focuser/', {
      method: 'GET',
    });
  }

  async getFhwm(): Promise<FhwmType> {
    return this.request<FhwmType>('/observation/fwhm', {
      method: 'GET',
    });
  }

  async setFocuserPosition(position: number): Promise<number> {
    return this.request<number>(`/focuser/${position}`, {
      method: 'POST',
    });
  }

  async focuserHalt(): Promise<void> {
    this.request<void>(`/focuser/stop`, {
      method: 'POST',
    });
  }


  async getFocus(): Promise<FwhmResults> {
    return this.request<FwhmResults>(`/focuser/lastfocus`, {
      method: 'GET',
    });
  }

  async startAutoFocus(): Promise<void> {
    this.request<void>(`/focuser/autofocus`, {
      method: 'PUT',
    });
  }


  async getOperationStatus(): Promise<number> {
    return this.request<number>('/status/operation_status',
      {method:"GET"}
    )
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
