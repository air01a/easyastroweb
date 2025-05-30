'use server';

import { setObserverLocation } from "@/lib/astro/observer/observer";

export async function setLocation(lat: number, lon: number) {
  // Simulate saving the location to a database or file
  // In a real application, you would replace this with actual logic
  console.log(`Location set to Latitude: ${lat}, Longitude: ${lon}`);
  setObserverLocation(lat, lon);
  // Return a success message
  return { success: true, message: 'Location updated successfully' };
}