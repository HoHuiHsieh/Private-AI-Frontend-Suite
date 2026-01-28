import { DataGrid } from '@mui/x-data-grid';
import { GridRowsProp, GridColDef } from '@mui/x-data-grid';


/**
 * CustomizedDataGrid component
 * @param param0 
 * @returns 
 */
export default function CustomizedDataGrid({columns, rows}: {columns: GridColDef[]; rows: GridRowsProp}) {
  return (
    <DataGrid
      rows={rows}
      columns={columns}
      getRowClassName={(params) =>
        params.indexRelativeToCurrentPage % 2 === 0 ? 'even' : 'odd'
      }
      initialState={{
        pagination: { paginationModel: { pageSize: 20 } },
      }}
      pageSizeOptions={[10, 20, 50]}
      disableColumnResize
      density="compact"
      slotProps={{
        filterPanel: {
          filterFormProps: {
            logicOperatorInputProps: {
              variant: 'outlined',
              size: 'small',
            },
            columnInputProps: {
              variant: 'outlined',
              size: 'small',
              sx: { mt: 'auto' },
            },
            operatorInputProps: {
              variant: 'outlined',
              size: 'small',
              sx: { mt: 'auto' },
            },
            valueInputProps: {
              InputComponentProps: {
                variant: 'outlined',
                size: 'small',
              },
            },
          },
        },
        pagination: {
          sx: {
            fontSize: '1rem',
          },
        },
      }}
    />
  );
}
