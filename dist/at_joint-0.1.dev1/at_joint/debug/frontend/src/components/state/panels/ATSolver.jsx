import { Button, Collapse, Empty, Popover, Skeleton, Tag, Table, Typography, Divider, Card } from "antd";

const WMState = ({ wm }) => {
    if (!wm || !Object.keys(wm).length) {
        return <Empty description="Рабочая память пуста" />;
    }
    const dataSource = Object.entries(wm).map(([key, value]) => ({
        ref: key,
        value: value.content,
        nonFactor: value.non_factor,
    }));
    return (
        <Table
            style={{ width: "100%" }}
            size="small"
            dataSource={dataSource}
            columns={[
                {
                    dataIndex: "ref",
                    title: "Имя",
                },
                {
                    dataIndex: "value",
                    title: "Значение",
                    render: (text) => <Tag>{text}</Tag>,
                },
                {
                    dataIndex: "nonFactor",
                    title: "НЕ-факторы",
                    render: (nf) => (
                        <>
                            УВЕРЕННОСТЬ{" "}
                            <b>
                                [{nf?.belief}; {nf?.probability}] ТОЧНОСТЬ {nf.accuracy}
                            </b>
                        </>
                    ),
                },
            ]}
        />
    );
};

const Trace = ({ steps }) => {
    return steps?.length ? (
        steps.map((step, i) => (
            <Collapse
                items={[
                    {
                        label: (
                            <>
                                Шаг {i + 1}. Применено правило: <b>{step.selected_rule}</b>
                            </>
                        ),
                        children: (
                            <table>
                                <tbody>
                                    <tr>
                                        <td>
                                            <b>
                                                Выполнены инструкции для случая <i>ТО/ИНАЧЕ</i>
                                            </b>
                                        </td>
                                        <td>
                                            {step.rule_condition_value ? (
                                                <Tag color="green">
                                                    <b>ТО</b>
                                                </Tag>
                                            ) : (
                                                <Tag color="red">
                                                    <b>ИНАЧЕ</b>
                                                </Tag>
                                            )}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td>
                                            <b>Конфликтные правила</b>
                                        </td>
                                        <td>
                                            {step.conflict_rules.map((r) => (
                                                <Tag color="orange">{r}</Tag>
                                            ))}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td>
                                            <b>Выполненые ранее правила</b>
                                        </td>
                                        <td>
                                            {step.fired_rules
                                                .filter((r) => r !== step.selected_rule)
                                                .map((r) => (
                                                    <Tag color="cyan">{r}</Tag>
                                                ))}
                                        </td>
                                    </tr>
                                    <tr>
                                        <td>
                                            <b>Состояние рабочей памяти до выполнения правила</b>
                                        </td>
                                        <td>
                                            <Popover
                                                trigger="click"
                                                title="Состояние РП"
                                                content={<WMState wm={step?.initial_wm_state} />}
                                            >
                                                <Button type="link">Показать состояние РП</Button>
                                            </Popover>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td>
                                            <b>Состояние рабочей памяти после выполнения правила</b>
                                        </td>
                                        <td>
                                            <Popover
                                                trigger="click"
                                                title="Состояние РП"
                                                content={<WMState wm={step?.final_wm_state} />}
                                            >
                                                <Button type="link">Показать состояние РП</Button>
                                            </Popover>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        ),
                    },
                ]}
            />
        ))
    ) : (
        <Empty description="Трасса вывода пуста" />
    );
};

const ATSolver = ({ atSolver, inferenceNow }) => {
    return !atSolver ? (
        !inferenceNow ? (
            <Empty description="Ожидание начала совместного функционирования" />
        ) : (
            <Skeleton active />
        )
    ) : (
        <div>
            <Typography.Title level={3}>Трасса вывода</Typography.Title>
            <Trace steps={atSolver?.trace?.steps} />
            <Divider />
            <Card title="Финальное состояние рабочей памяти">
                <WMState wm={atSolver?.wm} />
            </Card>
        </div>
    );
};

export default ATSolver;
