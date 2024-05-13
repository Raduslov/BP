
import React from "react";

// reactstrap components
import { Container, Nav, NavItem, NavLink } from "reactstrap";

function Footer() {
  return (
    <footer className="footer">
      <Container fluid>
        <Nav>
          <NavItem>
            <NavLink href="mailto:radoslav.jozef.hasul@student.tuke.sk">
             Email
            </NavLink>
          </NavItem>
          <NavItem>
          </NavItem>
          <NavItem>
            <NavLink href="https://github.com/Raduslov/BP">
           Git
            </NavLink>
          </NavItem>
        </Nav>
        <div className="copyright">
        Radoslav Jozef Hašuľ-Evidenčný systém pre EEG signály
        </div>
      </Container>
    </footer>
  );
}

export default Footer;
