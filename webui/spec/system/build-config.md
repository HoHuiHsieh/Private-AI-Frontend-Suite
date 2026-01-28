# Build Configuration

## 1. Purpose
The build configuration defines how the webui application is built for static file hosting using Next.js and related tools.

## 2. Requirements
- Next.js static export building
- TypeScript compilation
- Code linting and quality checks
- Development and production builds
- Static asset optimization for web hosting

## 3. Design
- **Build Tool**: Next.js with webpack
- **Language**: TypeScript with strict checking
- **Linting**: ESLint with Next.js rules
- **Package Management**: npm with package-lock.json

## 4. Next.js Configuration (next.config.js)

### Build Settings
- **Output**: Static export for static file hosting
- **Dist Directory**: `out/` for production builds
- **Image Optimization**: Disabled for static export (unoptimized: true)
- **SWC Compiler**: Fast TypeScript/JavaScript compilation

### Development Settings
- **Watch Mode**: File watching with WATCHPACK_POLLING
- **Hot Reload**: Automatic browser refresh
- **Source Maps**: Development debugging support

### Production Settings
- **Static Export**: Generate static HTML/CSS/JS files in `out/` directory
- **No Server**: Client-side only, no Node.js server required
- **CDN Ready**: Optimized for static file hosting and CDNs

## 5. TypeScript Configuration (tsconfig.json)

### Compiler Options
- **Target**: ES2017 for modern browsers
- **Module**: ESNext modules
- **JSX**: React JSX transform
- **Strict Mode**: Full TypeScript strict checking

### Path Mapping
- **@ alias**: src/ directory alias
- **Absolute Imports**: Clean import paths
- **Type Definitions**: Custom type declarations

### Build Info
- **tsconfig.tsbuildinfo**: Incremental compilation cache
- **Type Checking**: Build-time type validation

## 6. ESLint Configuration (.eslintrc.json)

### Rules
- **Next.js Rules**: next/core-web-vitals
- **React Rules**: React best practices
- **TypeScript Rules**: TypeScript-specific linting
- **Import Rules**: Clean import organization

### Extends
- **next/core-web-vitals**: Next.js recommended rules
- **@typescript-eslint**: TypeScript ESLint rules

## 7. Package Scripts

### Development
- **dev**: Development server with hot reload
- **lint**: Code linting and fixing
- **type-check**: TypeScript type checking

### Production
- **build**: Production static build generation
- **lint**: Code quality checks

## 8. Integration
- **CI/CD**: Automated build pipelines
- **Static Hosting**: Deploy `out/` directory to any web server or CDN
- **Deployment**: Vercel, Netlify, AWS S3, or traditional web hosting