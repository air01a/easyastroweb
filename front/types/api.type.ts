export type PlanType = {
  start: number;
  expo: number;
  nExpo: number,
  ra: number;
  dec: number;
  filter: string;
  object: string;
  focus: boolean;
};


export type DarkLibraryType = {
    gain: number
    temperature: number
    exposition: number
    count: number
}

export type DarkLibraryProcessType = DarkLibraryType & {
    eta: number;
    done: boolean;
    in_progress: boolean;
}