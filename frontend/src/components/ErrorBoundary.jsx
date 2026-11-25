import { Component } from "react";

// If any part of a page crashes, show what went wrong instead of a blank screen.
export default class ErrorBoundary extends Component {
  state = { error: null };
  static getDerivedStateFromError(error) {
    return { error };
  }
  componentDidCatch(error, info) {
    console.error("UI crashed:", error, info?.componentStack);
  }
  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="notice notice-warn" role="alert">
        <strong>Something on this page broke.</strong>
        <p style={{ margin: "6px 0 10px" }}>{String(this.state.error.message || this.state.error)}</p>
        <button className="btn btn-ghost btn-sm" onClick={() => this.setState({ error: null })}>Try again</button>
      </div>
    );
  }
}
