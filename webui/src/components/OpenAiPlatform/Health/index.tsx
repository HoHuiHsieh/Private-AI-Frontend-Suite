import { useState, useEffect } from 'react';
import Grid from '@mui/material/Grid';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import TextField from '@mui/material/TextField';
import IconButton from '@mui/material/IconButton';
import RefreshIcon from '@mui/icons-material/Refresh';
import StatCard, { StatCardProps } from '../StatCard';
import GPUStatusPieCard, { GPUStatusPieCardProps } from './PieCard';
import { usageService } from '@/services/usage';
import { padDailyData } from '../utils';


const api_overview_data: StatCardProps[] = [
    {
        title: 'Total Tokens',
        value: '1000000',
        interval: 'Last 30 days',
        trend: 'up',
        data: [],
    },
    {
        title: 'Total Requests',
        value: '100',
        interval: 'Last 30 days',
        trend: 'down',
        data: [],
    },
];

const api_capabilities_data: StatCardProps[] = [
    {
        title: 'openai/gpt-oss-20b',
        value: '40',
        interval: 'Last 30 days',
        trend: 'up',
        data: [],
    },
    {
        title: 'google/embeddinggemma-300m',
        value: '60',
        interval: 'Last 30 days',
        trend: 'neutral',
        data: [],
    },
];

const gpu_status_data: GPUStatusPieCardProps[] = [
    {
        label: 'GPU 1',
        memoryUsage: 8,
        totalMemory: 16,
        gpuBusy: 40,
    },
    {
        label: 'GPU 2',
        memoryUsage: 12,
        totalMemory: 16,
        gpuBusy: 60,
    },
];


/**
 * Usage component
 * @returns 
 */
export default function Health() {
    const [overviewData, setOverviewData] = useState<StatCardProps[]>(api_overview_data);
    const [capabilitiesData, setCapabilitiesData] = useState<StatCardProps[]>(api_capabilities_data);
    // const [gpuData, setGpuData] = useState<GPUStatusPieCardProps[]>(gpu_status_data);
    const [loading, setLoading] = useState(false);
    const [interval, setIntervalState] = useState<'day' | 'week' | 'month'>('day');
    const [period, setPeriod] = useState<number>(7);

    useEffect(() => {
        fetchHealthData();
        // fetchGPUStatus();
        return () => { };
    }, [interval, period]);

    const calculateDays = () => {
        switch (interval) {
            case 'day':
                return period;
            case 'week':
                return period * 7;
            case 'month':
                return period * 30;
            default:
                return 30;
        }
    };

    const getIntervalLabel = () => {
        const unit = period === 1 ? interval : `${interval}s`;
        return `Last ${period} ${unit}`;
    };

    const fetchHealthData = async () => {
        try {
            setLoading(true);
            const days = calculateDays();
            const intervalLabel = getIntervalLabel();
            const params = { days, interval, period };

            // Fetch system overview
            const overview = await usageService.getSystemOverview(params);
            // pad daily tokens from period_start to period_end if missing dates
            const daily_overview_tokens = padDailyData( overview.daily_data, overview.period_start, overview.period_end, 'tokens');
            const daily_overview_requests = padDailyData( overview.daily_data, overview.period_start, overview.period_end, 'requests');

            setOverviewData([
                {
                    title: 'Total Tokens',
                    value: overview.total_tokens.toLocaleString(),
                    interval: intervalLabel,
                    trend: daily_overview_tokens[daily_overview_tokens.length - 1].value > daily_overview_tokens[0].value ? 'up' : 'down',
                    data: daily_overview_tokens,
                },
                {
                    title: 'Total Requests',
                    value: overview.total_requests.toLocaleString(),
                    interval: intervalLabel,
                    trend: daily_overview_requests[daily_overview_requests.length - 1].value > daily_overview_requests[0].value ? 'up' : 'down',
                    data: daily_overview_requests,
                },
            ]);

            // Fetch model usage
            const modelUsage = await usageService.getSystemModelUsage(params);
            setCapabilitiesData(
                modelUsage.map(item => {
                    // pad daily data
                    const daily_model_tokens = padDailyData( 
                        item.daily_data, 
                        item.period_start, 
                        item.period_end, 
                        'tokens'
                    );
                    return {
                        title: `${item.model_name} Tokens`,
                        value: item.total_tokens.toLocaleString(),
                        interval: intervalLabel,
                        trend: daily_model_tokens[daily_model_tokens.length - 1].value > daily_model_tokens[0].value ? 'up' : 'down',
                        data: daily_model_tokens,
                    };
                })
            );

            // Fetch GPU status
            // await fetchGPUStatus();
        } catch (error) {
            console.error('Failed to fetch health data:', error);
            // Keep showing sample data on error
        } finally {
            setLoading(false);
        }
    };

    // const fetchGPUStatus = async () => {
    //     try {
    //         const gpus = await usageService.getGPUStatus();
    //         setGpuData(
    //             gpus.map(gpu => ({
    //                 label: gpu.label,
    //                 memoryUsage: gpu.memory_used_gb,
    //                 totalMemory: gpu.memory_total_gb,
    //                 gpuBusy: gpu.utilization_percent,
    //             }))
    //         );
    //     } catch (error) {
    //         console.error('Failed to fetch GPU status:', error);
    //     }
    // };

    return (
        <Box sx={{ width: '100%', maxWidth: { sm: '100%', md: '1700px' }, p: 4 }}>
            {/* Time Range Selectors */}
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mb: 3 }}>
                <TextField
                    label="Period"
                    type="number"
                    value={period}
                    onChange={(e) => setPeriod(Math.max(1, parseInt(e.target.value) || 1))}
                    slotProps={{
                        input: { inputProps: { min: 1, max: 365 } }
                    }}
                    sx={{ width: 120 }}
                    size="small"
                />
                <FormControl sx={{ width: 150 }} size="small">
                    <InputLabel>Interval</InputLabel>
                    <Select
                        value={interval}
                        label="Interval"
                        onChange={(e) => setIntervalState(e.target.value as 'day' | 'week' | 'month')}
                    >
                        <MenuItem value="day">Day(s)</MenuItem>
                        <MenuItem value="week">Week(s)</MenuItem>
                        <MenuItem value="month">Month(s)</MenuItem>
                    </Select>
                </FormControl>
                <IconButton
                    onClick={fetchHealthData}
                    disabled={loading}
                    color="primary"
                    aria-label="refresh health data"
                    sx={{
                        '&:hover': {
                            backgroundColor: 'action.hover',
                        },
                    }}
                >
                    <RefreshIcon sx={{
                        animation: loading ? 'spin 1s linear infinite' : 'none',
                        '@keyframes spin': {
                            '0%': { transform: 'rotate(0deg)' },
                            '100%': { transform: 'rotate(360deg)' },
                        },
                        fontSize: '1.5rem',
                    }} />
                </IconButton>
            </Box>

            {/* API Overview */}
            <Typography component="h2" variant="h6" sx={{ mb: 2 }}>
                API Overview
            </Typography>
            <Grid
                container
                spacing={2}
                columns={12}
                sx={{ mb: (theme) => theme.spacing(2) }}
            >
                {overviewData.map((card, index) => (
                    <Grid key={index} size={{ xs: 12, sm: 6, lg: 3 }}>
                        <StatCard {...card} />
                    </Grid>
                ))}
            </Grid>

            {/* API capabilities */}
            <Typography component="h2" variant="h6" sx={{ mb: 2 }}>
                API capabilities
            </Typography>
            <Grid
                container
                spacing={2}
                columns={12}
                sx={{ mb: (theme) => theme.spacing(2) }}
            >
                {capabilitiesData.map((card, index) => (
                    <Grid key={index} size={{ xs: 12, sm: 6, lg: 3 }}>
                        <StatCard {...card} />
                    </Grid>
                ))}
            </Grid>

            {/* GPU Status */}
            {/* <Typography component="h2" variant="h6" sx={{ mb: 2 }}>
                GPU Status
            </Typography>
            <Grid
                container
                spacing={2}
                columns={12}
            // sx={{ mb: (theme) => theme.spacing(2) }}
            >
                {gpuData.map((card, index) => (
                    <Grid key={index} size={{ xs: 12, sm: 6, lg: 4 }}>
                        <GPUStatusPieCard {...card} />
                    </Grid>
                ))}
            </Grid> */}
        </Box>
    );
}
