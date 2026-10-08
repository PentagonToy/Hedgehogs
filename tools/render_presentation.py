"""Compare ordinary rendering and plots.show(): python tools/render_presentation.py OUTPUT_DIRECTORY."""
import argparse
import warnings
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import hedgehogs as hdg


def render(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    operations = ['read csv', 'aggregations', 'window functions', 'inner join', 'left join', 'full join']
    polars = [.79, .04, .65, .11, .51, 1.16]
    pandas = [16.03, .5, 9.48, 4.98, 11.91, 14.12]
    hdg.set_style()
    for horizontal in (False, True):
        fig, ax = plt.subplots(figsize=(7, 4.5))
        first_positions = [index - .175 for index in range(6)]
        second_positions = [index + .175 for index in range(6)]
        if horizontal:
            first = ax.barh(first_positions, polars, .35, label='Polars')
            second = ax.barh(second_positions, pandas, .35, label='Pandas')
            ax.set_yticks(range(6), operations)
            ax.invert_yaxis()
            ax.set(xlabel='Time [s]', xlim=(0, max(pandas) * 1.18))
        else:
            first = ax.bar(first_positions, polars, .35, label='Polars')
            second = ax.bar(second_positions, pandas, .35, label='Pandas')
            ax.set_xticks(range(6), operations)
            ax.set(ylabel='Time [s]')
        ax.bar_label(first, fmt='%.2f', padding=3)
        ax.bar_label(second, fmt='%.2f', padding=3)
        ax.set_title('Speed Comparison')
        ax.legend(loc='center right')
        fig.tight_layout()
        name = 'horizontal' if horizontal else 'vertical'
        fig.savefig(output / f'{name}_before.png', dpi=200)
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', message='FigureCanvasAgg is non-interactive')
            hdg.plots.show(fig, block=False)
        for suffix in ('png', 'pdf', 'svg'):
            fig.savefig(output / f'{name}_after.{suffix}', dpi=200)
        plt.close(fig)
    hdg.reset_style()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    render(parser.parse_args().output)
