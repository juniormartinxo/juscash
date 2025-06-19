import { TbClockDollar } from "react-icons/tb"

const Spin = ({ h, w }: { h: number, w: number }) => {
    return (
        <TbClockDollar className={`animate-spin text-primary h-${h} w-${w}`} />
    )
}

Spin.displayName = 'Spin'

export default Spin