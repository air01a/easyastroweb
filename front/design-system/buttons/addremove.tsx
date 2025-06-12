import { Plus, Trash } from 'lucide-react';
import { forwardRef } from 'react';
import type { ButtonHTMLAttributes } from 'react';
type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement>;

export const AddButton = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = '', ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={`text-green-600 hover:text-green-800 transform transition-transform duration-150 hover:scale-105 ${className}`}
        {...props}
      ><Plus size={20} />
      </button>
    );
  }
);

AddButton.displayName = 'AddInput';

export const RemoveButton = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = '', ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={`text-red-600 hover:text-red-800 transform transition-transform duration-150 hover:scale-110 ${className}`}
        {...props}
      > <Trash size={20} />
      </button>
    );
  }
);

RemoveButton.displayName = 'AddInput';


