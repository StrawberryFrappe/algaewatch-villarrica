import { Component } from 'react';

// A render error anywhere below this boundary used to unmount the entire app:
// React 18 tears the whole tree down when nothing catches, so a zero-width
// canvas inside the heat layer left the dashboard as a blank page with the
// error visible only in the console. During a live demo that is the worst
// possible failure mode — everything disappears and nothing says why.
//
// The boundary keeps the failure local: the surrounding views keep working and
// the broken region says what happened. It is not a substitute for fixing the
// underlying bug (see HeatLayer's zero-size guard), it is the seatbelt.
export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    // Left as console output on purpose: this project has no error-reporting
    // backend, and inventing one here would be scope the dashboard does not own.
    console.error('[ErrorBoundary]', this.props.label ?? 'unlabelled', error, info);
  }

  render() {
    if (!this.state.error) return this.props.children;

    return (
      <div
        role="alert"
        style={{
          padding: '14px 16px',
          border: '1px solid var(--hairline)',
          borderRadius: 10,
          background: 'var(--color-surface, transparent)',
          fontSize: 12.5,
          lineHeight: 1.5,
          color: 'var(--color-text-dim)',
        }}
      >
        <div style={{ color: 'var(--color-text-tertiary-2)', fontWeight: 600, marginBottom: 4 }}>
          {this.props.label ?? 'Este componente'} no se pudo mostrar.
        </div>
        El resto del panel sigue funcionando. Detalle técnico en la consola del navegador.
      </div>
    );
  }
}
