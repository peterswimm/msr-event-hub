import { Caption1Strong, Link } from "@fluentui/react-components";

const Footer = () => {
  return (
    <div className="footer-container">
      <Link href="mailto:mcrinfo@microsoft.com" target="_blank" rel="noreferrer">
        <Caption1Strong className="footer-text">Contact Us</Caption1Strong>
      </Link>
      <Caption1Strong className="footer-text">|</Caption1Strong>
      <Link href="https://www.microsoft.com/en-us/legal/terms-of-use" target="_blank" rel="noreferrer">
        <Caption1Strong className="footer-text">Terms of Use</Caption1Strong>
      </Link>
      <Caption1Strong className="footer-text">|</Caption1Strong>
      <Link href="https://go.microsoft.com/fwlink/?LinkId=521839" target="_blank" rel="noreferrer">
        <Caption1Strong className="footer-text">Privacy & Cookies</Caption1Strong>
      </Link>
      <Caption1Strong className="footer-text">|</Caption1Strong>
      <Caption1Strong className="footer-text">© {new Date().getFullYear()} Microsoft</Caption1Strong>
    </div>
  );
};

export default Footer;
