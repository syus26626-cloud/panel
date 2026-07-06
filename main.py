import discord
from discord import app_commands
from discord.ext import commands
import os
from keep_alive import keep_alive # keepファイルをインポート

# 指定された環境変数名で取得
TOKEN = os.environ.get("DISCORD_TOKEN")

intents = discord.Intents.default()

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Botが再起動しても、設置済みのパネルがずっと反応し続けるように永続化
        self.add_view(RolePanelView())

bot = MyBot()

# ─── ロールセレクトメニュー（ID不要・自動選択式） ───
class RoleDropdown(discord.ui.RoleSelect):
    def __init__(self):
        super().__init__(
            placeholder="ここをタップしてロールを選択...", 
            min_values=1, 
            max_values=5, 
            custom_id="persistent_role_panel_v6" # 一意のIDで永続化
        )

    async def callback(self, interaction: discord.Interaction):
        # 「考え中...」の非表示メッセージを出す
        await interaction.response.defer(ephemeral=True)
        
        member = interaction.user
        bot_member = interaction.guild.me
        log_messages = []

        for role in self.values:
            # Botが触れないロール（@everyoneや、Bot自身より上のロール）を安全にスルー
            if role.managed or role == interaction.guild.default_role or role.position >= bot_member.top_role.position:
                log_messages.append(f"⚠️ **{role.name}** はBotの権限が足りないため操作できません。")
                continue

            # ロールをすでに持っていれば外す、なければ付与する（トグル機能）
            if role in member.roles:
                await member.remove_roles(role)
                log_messages.append(f"❌ **{role.name}** を外しました。")
            else:
                await member.add_roles(role)
                log_messages.append(f"✅ **{role.name}** を付与しました。")

        # 結果を本人にだけ通知
        await interaction.followup.send(
            "\n".join(log_messages) if log_messages else "変更はありませんでした。", 
            ephemeral=True
        )

class RolePanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(RoleDropdown())

# ─── 起動イベントとスラッシュコマンド ───
@bot.event
async def on_ready():
    print(f"{bot.user.name} が起動しました！")
    try:
        # スラッシュコマンドをDiscordサーバー側へ同期
        synced = await bot.tree.sync()
        print(f"{len(synced)} 個のコマンドを同期しました。")
    except Exception as e:
        print(f"同期失敗: {e}")

# /コマンド化 ＆ タイトルや説明文をその場で決められる機能
@bot.tree.command(name="make-panel", description="ロール選択パネルを作成します")
@app_commands.describe(title="パネルのタイトル（名前）", description="パネルの説明文（省略可能）")
async def make_panel(interaction: discord.Interaction, title: str, description: str = None):
    # 実行者にロール管理権限があるか確認
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("❌ ロール管理権限がないため実行できません。", ephemeral=True)
        return

    if description is None:
        description = "下のメニューから欲しいロールを選んでください。\n※既に持っているロールを選ぶと外れます。"

    embed = discord.Embed(title=title, description=description, color=discord.Color.brand_green())
    
    # チャンネルにパネルを送信
    await interaction.channel.send(embed=embed, view=RolePanelView())
    await interaction.response.send_message("✅ パネルを作成しました！", ephemeral=True)

# 1. バックグラウンドでFlaskサーバーを起動（常時起動用窓口）
keep_alive()

# 2. Discord Botを起動
bot.run(TOKEN)
