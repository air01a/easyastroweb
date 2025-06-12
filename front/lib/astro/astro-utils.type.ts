interface AltitudeGraphTypeItem {
    time: number; altitude: number; azimuth: number; visibility : VisibilityStatus | null;
}

export type VisibilityStatus = 'visible' | 'non-visible' | 'partially-visible' | 'masked' ;
export type AltitudeGraphType = AltitudeGraphTypeItem[];