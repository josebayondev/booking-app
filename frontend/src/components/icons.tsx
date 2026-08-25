// Iconos de línea mínimos, dibujados a mano: el proyecto no tiene una librería de iconos
// y no compensa añadir una dependencia para cuatro trazos.
import type { SVGProps } from 'react'

export function CalendarIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <rect x="3" y="4.5" width="14" height="12" rx="2" />
      <path d="M3 8.5h14M7 2.5v3M13 2.5v3" />
    </svg>
  )
}

export function ClockIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <circle cx="10" cy="10" r="7" />
      <path d="M10 6.5V10l2.5 1.5" />
    </svg>
  )
}

export function CheckIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <circle cx="10" cy="10" r="7" />
      <path d="M7 10l2 2 4-4" />
    </svg>
  )
}

export function ListIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M4 6h3M4 10h3M4 14h3" />
      <path d="M9 6h7M9 10h7M9 14h7" />
    </svg>
  )
}
