import { theme } from "antd";
import mobileCheck from "./mobileCheck";

export default ({ children, style, ...props }) => {
    const {
        token: { colorBgContainer },
    } = theme.useToken();
    return (
        <div
            style={{
                marginTop: mobileCheck() ? 15 : 24,
                height: "100%",
                padding: mobileCheck() ? 15 : 24,
                background: colorBgContainer,
                ...style,
            }}
            {...props}
        >
            {children}
        </div>
    );
};

export const ThemedBar = ({ children, style, ...props }) => {
    const {
        token: { colorBgContainer },
    } = theme.useToken();
    return (
        <div
            style={{
                marginTop: mobileCheck() ? 15 : 24,
                padding: mobileCheck() ? 15 : 24,
                background: colorBgContainer,
                ...style,
            }}
            {...props}
        >
            {children}
        </div>
    );
};
