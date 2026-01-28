import React from 'react';
import { PieChart } from '@mui/x-charts/PieChart';
import Typography from '@mui/material/Typography';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Stack from '@mui/material/Stack';
import PieCenterLabel from './PieCenterLabel';

// const mem_data = [
//     { label: 'GPU Memory', value: 80 },
//     { label: '', value: 20 },
// ];
// const busy_data = [
//     { label: 'GPU Busy', value: 40 },
//     { label: '', value: 60 },
// ];

const colors_mem = [
    'hsla(217, 100%, 50%, 1.00)',
    'hsl(220, 20%, 65%)',
];

const colors_busy = [
    'hsla(40, 100%, 50%, 1.00)',
    'hsl(220, 20%, 65%)',
];


export interface GPUStatusPieCardProps {
    label: string;
    memoryUsage: number;
    totalMemory: number;
    gpuBusy: number;
}
/**
 * GPUStatusPieCard component
 * @returns 
 */
export default function GPUStatusPieCard(props: GPUStatusPieCardProps) {
    const { label, memoryUsage, totalMemory, gpuBusy } = props;
    if (!memoryUsage || !totalMemory || !gpuBusy) {
        return null;
    }

    // Prepare data for the pie charts
    const mem_data = [
        { label: `Used: ${memoryUsage} GB`, value: memoryUsage },
        { label: `Free: ${totalMemory - memoryUsage} GB`, value: totalMemory - memoryUsage },
    ];
    const busy_data = [
        { label: `Busy: ${gpuBusy}%`, value: gpuBusy },
        { label: `Idle: ${100 - gpuBusy}%`, value: 100 - gpuBusy },
    ];

    return (
        <Card
            variant="outlined"
            sx={{ display: 'flex', flexDirection: 'column', gap: '8px', flexGrow: 1 }}
        >
            <CardContent>
                <Typography component="h2" variant="subtitle2">
                    {label}
                </Typography>
                <Stack direction="row" sx={{ gap: 2, mb: 2 }}>
                    <CustomPieChart
                        label="Memory"
                        colors={colors_mem}
                        data={mem_data}
                    />
                    <CustomPieChart
                        label="Load"
                        colors={colors_busy}
                        data={busy_data}
                    />
                </Stack>
            </CardContent>
        </Card>
    );
}


interface CustomPieChartProps {
    label: string;
    colors: string[];
    data: { label: string; value: number }[];
}

/**
 * 
 * @param param0 
 * @returns 
 */
function CustomPieChart({ label, colors, data }: CustomPieChartProps) {
    return (
        <PieChart
            colors={colors}
            margin={{
                left: 60,
                right: 60,
                top: 10,
                bottom: 60,
            }}
            series={[
                {
                    data,
                    innerRadius: 55,
                    outerRadius: 80,
                    // paddingAngle: 0,
                    highlightScope: { fade: 'global', highlight: 'item' },
                },
            ]}
            height={250}
            width={190}
            slotProps={{
                legend: {
                    direction: 'column',
                    position: { vertical: 'bottom', horizontal: 'middle' },
                    padding: 0,
                },
            }}
        >
            <PieCenterLabel primaryText={label} />
        </PieChart>
    )
}