import {ButtonHTMLAttributes, JSX} from "react";

export  interface NavbarButtonInterface extends ButtonHTMLAttributes<HTMLButtonElement> {
    name: string,
    href : string, 
    selected? : boolean,
    startIcon?: null | JSX.Element,
    matcher?:string,
    background?:string

}

export interface NavBarInterface {
    currentRoute: string
}

export interface NavBarProps {
    menu: NavbarButtonInterface[];
}