import { useState } from "react";
import Icon from "./Icon";

export default function PasswordInput({ id, name, value, onChange, placeholder, autoComplete }) {
  const [show, setShow] = useState(false);
  return (
    <div className="pw">
      <input
        id={id} name={name} className="input" type={show ? "text" : "password"}
        value={value} onChange={onChange} placeholder={placeholder} autoComplete={autoComplete} required
      />
      <button type="button" className="pw-toggle" onClick={() => setShow((s) => !s)}
        aria-label={show ? "Hide password" : "Show password"}>
        <Icon name={show ? "eyeoff" : "eye"} />
      </button>
    </div>
  );
}
