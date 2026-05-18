import plotly.express as px

def bar_chart(df, x, y, title):
    fig = px.bar(
        df,
        x=x,
        y=y,
        title=title,
        template="plotly_dark"
    )

    fig.update_layout(
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        font_color="#ffffff",
        title_font_size=16,
        margin=dict(l=20, r=20, t=50, b=20),
        height=320
    )

    return fig