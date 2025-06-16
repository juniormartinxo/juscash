import { memo } from 'react'

interface LogoProps {
  /**
   * Tamanho customizado para width e height
   */
  size?: number | string
  /**
   * Width customizado (sobrescreve size se fornecido)
   */
  width?: number | string
  /**
   * Height customizado (sobrescreve size se fornecido)
   */
  height?: number | string
  /**
   * Classes CSS adicionais
   */
  className?: string
  /**
   * Alt text para acessibilidade
   */
  alt?: string
  /**
   * Callback para cliques no logo
   */
  onClick?: () => void
  /**
   * Se o logo deve ser clicável (cursor pointer)
   */
  clickable?: boolean
}

/**
 * Componente Logo - Renderiza o logo da aplicação usando SVG
 * 
 * @param props - Propriedades do componente
 * @returns JSX.Element
 */
const Logo = memo<LogoProps>(({
  size = 120,
  width,
  height,
  className = '',
  alt = 'JusCash Logo',
  onClick,
  clickable = false
}) => {
  const logoWidth = width ?? size
  const logoHeight = height ?? size
  
  const logoClasses = [
    'inline-block',
    clickable || onClick ? 'cursor-pointer' : '',
    className
  ].filter(Boolean).join(' ')

  const handleClick = () => {
    if (onClick) {
      onClick()
    }
  }

  return (
    <img
      src="/logo.svg"
      alt={alt}
      width={logoWidth}
      height={logoHeight}
      className={logoClasses}
      onClick={handleClick}
      draggable={false}
      style={{
        maxWidth: '100%',
        height: 'auto'
      }}
    />
  )
})

Logo.displayName = 'Logo'

export default Logo