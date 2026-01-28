// Utility function to pad daily data with missing dates
export function padDailyData(dailyData: { date: string, [key: string]: any }[], periodStart: string, periodEnd: string, valueKey: string): { date: string, value: number }[] {
    const startDate = new Date(periodStart);
    startDate.setDate(startDate.getDate() + 1); // Skip the first day
    const endDate = new Date(periodEnd);
    const dataMap = new Map(dailyData.map(d => [d.date, d[valueKey]]));
    const result: { date: string, value: number }[] = [];

    for (let date = new Date(startDate); date <= endDate; date.setDate(date.getDate() + 1)) {
        const dateStr = date.toISOString().split('T')[0];
        const value = dataMap.get(dateStr) || 0;
        result.push({ date: dateStr, value });
    }

    return result;
}
