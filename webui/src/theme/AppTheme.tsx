import * as React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import type { ThemeOptions } from '@mui/material/styles';
import { inputsCustomizations } from './customizations/inputs';
import { dataDisplayCustomizations } from './customizations/dataDisplay';
import { feedbackCustomizations } from './customizations/feedback';
import { navigationCustomizations } from './customizations/navigation';
import { surfacesCustomizations } from './customizations/surfaces';
import { colorSchemes, typography, shadows, shape } from './themePrimitives';
import { useUser } from '@/context/UserProvider';

interface AppThemeProps {
  children: React.ReactNode;
  /**
   * This is for the docs site. You can ignore it or remove it.
   */
  disableCustomTheme?: boolean;
  themeComponents?: ThemeOptions['components'];
}

const getFontSizeScale = (fontSize: 'small' | 'medium' | 'large') => {
  switch (fontSize) {
    case 'small':
      return 0.875; // 87.5% of default
    case 'large':
      return 1.125; // 112.5% of default
    case 'medium':
    default:
      return 1; // 100% default
  }
};

export default function AppTheme(props: AppThemeProps) {
  const { children, disableCustomTheme, themeComponents } = props;
  const { fontSize } = useUser();

  const theme = React.useMemo(() => {
    const fontSizeScale = getFontSizeScale(fontSize);
    
    return disableCustomTheme
      ? {}
      : createTheme({
          // For more details about CSS variables configuration, see https://mui.com/material-ui/customization/css-theme-variables/configuration/
          cssVariables: {
            colorSchemeSelector: 'data-mui-color-scheme',
            cssVarPrefix: 'template',
          },
          colorSchemes, // Recently added in v6 for building light & dark mode app, see https://mui.com/material-ui/customization/palette/#color-schemes
          typography: {
            ...typography,
            fontSize: 28 * fontSizeScale,
            h1: { ...typography.h1, fontSize: `${2.5 * fontSizeScale}rem` },
            h2: { ...typography.h2, fontSize: `${2 * fontSizeScale}rem` },
            h3: { ...typography.h3, fontSize: `${1.75 * fontSizeScale}rem` },
            h4: { ...typography.h4, fontSize: `${1.5 * fontSizeScale}rem` },
            h5: { ...typography.h5, fontSize: `${1.25 * fontSizeScale}rem` },
            h6: { ...typography.h6, fontSize: `${1 * fontSizeScale}rem` },
            body1: { ...typography.body1, fontSize: `${1 * fontSizeScale}rem` },
            body2: { ...typography.body2, fontSize: `${0.875 * fontSizeScale}rem` },
          },
          shadows,
          shape,
          components: {
            ...inputsCustomizations,
            ...dataDisplayCustomizations,
            ...feedbackCustomizations,
            ...navigationCustomizations,
            ...surfacesCustomizations,
            ...themeComponents,
          },
        });
  }, [disableCustomTheme, themeComponents, fontSize]);
  if (disableCustomTheme) {
    return <React.Fragment>{children}</React.Fragment>;
  }
  return (
    <ThemeProvider theme={theme} disableTransitionOnChange>
      {children}
    </ThemeProvider>
  );
}
