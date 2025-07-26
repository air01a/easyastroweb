export type PlanType = {
  start: number;
  expo: number;
  nExpo: number,
  ra: number;
  dec: number;
  filter: string;
  object: string;
  focus: boolean;
  gain: number;
};


export type DarkLibraryType = {
    gain: number
    temperature: number
    exposition: number
    count: number
    date?: string
}

export type DarkLibraryProcessType = DarkLibraryType & {
    eta: number;
    done: boolean;
    in_progress: boolean;
    progress: number;
}


export interface PlanHistory {
  start: number;
  expo: number;
  number: number;
  ra: number;
  dec: number;
  filter: string;
  object: string;
  focus: boolean;
  gain: number;
  real_start: string;
  end: string;
  images: number;
  jpg: string;
}

export type PlansHistory = PlanHistory[];