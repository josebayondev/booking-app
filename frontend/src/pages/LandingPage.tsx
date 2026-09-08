// Ruta `/`: la landing pública. Su único trabajo es componer -- tira del hook que hace
// falta y reparte contenido y datos entre las secciones. Ni copy ni lógica propia: el texto
// está en `content/landing.ts` y cada sección sabe pintarse sola.
import AppointmentTypes from '../components/sections/AppointmentTypes.tsx'
import Faq from '../components/sections/Faq.tsx'
import FinalCta from '../components/sections/FinalCta.tsx'
import Hero from '../components/sections/Hero.tsx'
import Process from '../components/sections/Process.tsx'
import Stats from '../components/sections/Stats.tsx'
import { landing } from '../content/landing.ts'
import { useAppointmentTypes } from '../features/appointmentTypes/useAppointmentTypes.ts'

export default function LandingPage() {
  const { data, isLoading, isError, refetch } = useAppointmentTypes()

  return (
    <div className="flex flex-col gap-24 pb-8">
      <Hero content={landing.hero} />
      <Stats items={landing.stats} />
      <Process content={landing.process} />
      <AppointmentTypes
        content={landing.appointmentTypes}
        types={data}
        isLoading={isLoading}
        isError={isError}
        onRetry={() => void refetch()}
      />
      <Faq content={landing.faq} />
      <FinalCta content={landing.finalCta} />
    </div>
  )
}
