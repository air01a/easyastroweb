import React from "react";
import { Loader2 } from "lucide-react";
import classNames from "classnames";

type LoadingIndicatorProps = {
  text?: string;
  className?: string;
};

const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({ text = "Chargement...", className }) => {
  return (
    <div className={classNames("flex items-center space-x-2 text-sm text-gray-500", className)}>
      <Loader2 className="animate-spin w-4 h-4" />
      <span>{text}</span>
    </div>
  );
};

export default LoadingIndicator;
