import { AlertTriangle } from "lucide-react";

export default function ServiceUnavailable() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center p-6">
      <AlertTriangle className="w-12 h-12 text-yellow-500 mb-4" />
      <h2 className="text-xl font-semibold mb-2">
        Connexion requise
      </h2>
      <p className="text-gray-600">
        Vous devez d’abord vous connecter au matériel du télescope 
        avant de pouvoir utiliser ce service.
      </p>
    </div>
  );
}
