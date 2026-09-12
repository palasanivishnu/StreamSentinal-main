import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  icon,
  className = '',
  disabled,
  ...props
}) => {
  let base =
    'inline-flex items-center justify-center font-sans font-semibold transition-all duration-150 rounded-xl cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500';
  let varStyle = 'bg-[#2563EB] hover:bg-blue-700 text-white shadow-xs';

  if (variant === 'secondary') {
    varStyle = 'bg-white hover:bg-[#F8FAFC] text-[#0F172A] border border-[#E2E8F0] shadow-xs';
  } else if (variant === 'danger') {
    varStyle = 'bg-[#DC2626] hover:bg-red-700 text-white shadow-xs';
  } else if (variant === 'success') {
    varStyle = 'bg-[#16A34A] hover:bg-emerald-700 text-white shadow-xs';
  } else if (variant === 'outline') {
    varStyle = 'border border-[#E2E8F0] hover:bg-[#F8FAFC] text-[#0F172A]';
  } else if (variant === 'ghost') {
    varStyle = 'hover:bg-slate-100 text-[#64748B] hover:text-[#0F172A]';
  }

  let sizeStyle = 'px-3.5 py-2 text-xs';
  if (size === 'sm') sizeStyle = 'px-2.5 py-1.5 text-xs';
  if (size === 'lg') sizeStyle = 'px-5 py-2.5 text-sm font-semibold';

  return (
    <button className={`${base} ${varStyle} ${sizeStyle} ${className}`} disabled={disabled || isLoading} {...props}>
      {isLoading ? (
        <span className="mr-2 h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
      ) : icon ? (
        <span className="mr-1.5">{icon}</span>
      ) : null}
      {children}
    </button>
  );
};