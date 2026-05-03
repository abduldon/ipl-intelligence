from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT

router = APIRouter(prefix="/export", tags=["Export"])

# ── COLOR PALETTE ──
DARK_BG    = colors.HexColor("#0f172a")
SURFACE    = colors.HexColor("#1e293b")
ACCENT     = colors.HexColor("#3b82f6")
ACCENT2    = colors.HexColor("#f59e0b")
GREEN      = colors.HexColor("#22c55e")
RED        = colors.HexColor("#ef4444")
TEXT       = colors.HexColor("#f1f5f9")
MUTED      = colors.HexColor("#94a3b8")
PURPLE     = colors.HexColor("#a855f7")
WHITE      = colors.white

class PlayerData(BaseModel):
    player: str
    impact_score: float
    batting_score: float
    bowling_score: float
    runs: int
    strike_rate: float
    wickets: int
    economy: float

class PhaseData(BaseModel):
    phase: str
    runs: float
    balls: float
    strike_rate: float
    fours: float
    sixes: float

class SeasonData(BaseModel):
    season: str
    matches: int
    runs: float
    strike_rate: float
    avg: float

class PlayerReportRequest(BaseModel):
    impact: PlayerData
    phases: List[PhaseData] = []
    seasons: List[SeasonData] = []

class SquadPlayer(BaseModel):
    player: str
    role: str
    price_paid: float
    impact_score: Optional[float] = 0
    runs: Optional[int] = 0
    wickets: Optional[int] = 0

class SquadReportRequest(BaseModel):
    players: List[SquadPlayer]
    total_purse: float = 120

class ComparePlayer(BaseModel):
    name: str
    impact_score: float
    batting_score: float
    bowling_score: float
    runs: int
    strike_rate: float
    wickets: int
    economy: float

class CompareReportRequest(BaseModel):
    player1: ComparePlayer
    player2: ComparePlayer

def dark_table_style(header_color=ACCENT):
    return TableStyle([
        ('BACKGROUND',   (0,0), (-1,0),  header_color),
        ('TEXTCOLOR',    (0,0), (-1,0),  WHITE),
        ('FONTNAME',     (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',     (0,0), (-1,0),  9),
        ('ALIGN',        (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS',(0,1),(-1,-1), [SURFACE, DARK_BG]),
        ('TEXTCOLOR',    (0,1), (-1,-1), TEXT),
        ('FONTNAME',     (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE',     (0,1), (-1,-1), 8),
        ('GRID',         (0,0), (-1,-1), 0.3, colors.HexColor("#334155")),
        ('ROWHEIGHT',    (0,0), (-1,-1), 22),
        ('TOPPADDING',   (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',(0,0), (-1,-1), 4),
    ])

def make_styles():
    s = getSampleStyleSheet()
    title = ParagraphStyle('Title', fontName='Helvetica-Bold', fontSize=22,
                           textColor=ACCENT, spaceAfter=4, alignment=TA_LEFT)
    subtitle = ParagraphStyle('Sub', fontName='Helvetica', fontSize=11,
                              textColor=MUTED, spaceAfter=16, alignment=TA_LEFT)
    section = ParagraphStyle('Section', fontName='Helvetica-Bold', fontSize=13,
                             textColor=ACCENT2, spaceBefore=16, spaceAfter=8)
    body = ParagraphStyle('Body', fontName='Helvetica', fontSize=9,
                          textColor=TEXT, spaceAfter=4)
    return title, subtitle, section, body

def header_block(story, title_text, sub_text, title_style, sub_style):
    story.append(Paragraph("🏏 IPL Intelligence Platform", ParagraphStyle(
        'Logo', fontName='Helvetica-Bold', fontSize=10, textColor=MUTED, spaceAfter=2)))
    story.append(Paragraph(title_text, title_style))
    story.append(Paragraph(sub_text, sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=16))

@router.post("/player-pdf")
async def export_player_pdf(req: PlayerReportRequest):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    title_s, sub_s, section_s, body_s = make_styles()
    p = req.impact

    header_block(story, p.player, f"Career Analytics Report  •  All IPL Seasons", title_s, sub_s)

    # Impact Score Hero
    story.append(Paragraph("Impact Score", section_s))
    impact_data = [
        ["Overall Impact", "Batting Score", "Bowling Score"],
        [str(p.impact_score), str(p.batting_score), str(p.bowling_score)],
    ]
    t = Table(impact_data, colWidths=[6*cm, 6*cm, 6*cm])
    ts = dark_table_style(ACCENT)
    ts.add('FONTSIZE',   (0,1), (-1,1), 18)
    ts.add('FONTNAME',   (0,1), (-1,1), 'Helvetica-Bold')
    ts.add('TEXTCOLOR',  (0,0), (0,1),  GREEN)
    ts.add('TEXTCOLOR',  (1,1), (1,1),  ACCENT)
    ts.add('TEXTCOLOR',  (2,1), (2,1),  ACCENT2)
    ts.add('ROWHEIGHT',  (0,1), (-1,1), 36)
    t.setStyle(ts)
    story.append(t)
    story.append(Spacer(1, 12))

    # Career Stats
    story.append(Paragraph("Career Statistics", section_s))
    stats_data = [
        ["Runs", "Strike Rate", "Avg/Match", "Wickets", "Economy"],
        [str(p.runs), str(p.strike_rate), "—", str(p.wickets), str(p.economy)],
    ]
    t2 = Table(stats_data, colWidths=[3.6*cm]*5)
    t2.setStyle(dark_table_style(ACCENT))
    story.append(t2)
    story.append(Spacer(1, 12))

    # Phase Breakdown
    if req.phases:
        story.append(Paragraph("Phase-wise Batting Breakdown", section_s))
        phase_data = [["Phase", "Runs", "Balls", "Strike Rate", "4s", "6s"]]
        colors_map = {"Powerplay": GREEN, "Middle": ACCENT, "Death": ACCENT2}
        for ph in req.phases:
            phase_data.append([ph.phase, str(int(ph.runs)), str(int(ph.balls)),
                                str(ph.strike_rate), str(int(ph.fours)), str(int(ph.sixes))])
        t3 = Table(phase_data, colWidths=[3.5*cm, 2.5*cm, 2.5*cm, 3*cm, 2*cm, 2*cm])
        ts3 = dark_table_style(SURFACE)
        for i, ph in enumerate(req.phases, 1):
            c = colors_map.get(ph.phase, TEXT)
            ts3.add('TEXTCOLOR', (0, i), (0, i), c)
            ts3.add('FONTNAME',  (0, i), (0, i), 'Helvetica-Bold')
        t3.setStyle(ts3)
        story.append(t3)
        story.append(Spacer(1, 12))

    # Season History
    if req.seasons:
        story.append(Paragraph("Season by Season Performance", section_s))
        season_data = [["Season", "Matches", "Runs", "Strike Rate", "Avg/Match"]]
        for s in req.seasons:
            season_data.append([f"IPL {s.season}", str(s.matches),
                                 str(int(s.runs)), str(s.strike_rate), str(s.avg)])
        t4 = Table(season_data, colWidths=[3*cm, 3*cm, 3*cm, 3.5*cm, 3.5*cm])
        t4.setStyle(dark_table_style(PURPLE))
        story.append(t4)

    story.append(Spacer(1, 20))
    story.append(Paragraph("Generated by IPL Intelligence Platform • For analyst use only",
                            ParagraphStyle('Footer', fontName='Helvetica', fontSize=7,
                                           textColor=MUTED, alignment=TA_CENTER)))
    doc.build(story)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/pdf",
                             headers={"Content-Disposition": f"attachment; filename={p.player.replace(' ','_')}_report.pdf"})


@router.post("/squad-pdf")
async def export_squad_pdf(req: SquadReportRequest):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    title_s, sub_s, section_s, body_s = make_styles()

    spent = sum(p.price_paid for p in req.players)
    remaining = req.total_purse - spent

    header_block(story, "Auction Squad Report",
                 f"{len(req.players)} players • ₹{spent:.1f}Cr spent • ₹{remaining:.1f}Cr remaining",
                 title_s, sub_s)

    # Budget summary
    story.append(Paragraph("Budget Overview", section_s))
    budget_data = [
        ["Total Purse", "Spent", "Remaining", "Players"],
        [f"₹{req.total_purse}Cr", f"₹{spent:.1f}Cr",
         f"₹{remaining:.1f}Cr", str(len(req.players))],
    ]
    bt = Table(budget_data, colWidths=[4.5*cm]*4)
    bts = dark_table_style(GREEN)
    bts.add('TEXTCOLOR', (0,1),(0,1), GREEN)
    bts.add('TEXTCOLOR', (1,1),(1,1), RED)
    bts.add('TEXTCOLOR', (2,1),(2,1), ACCENT)
    bts.add('FONTSIZE',  (0,1),(-1,1), 14)
    bts.add('FONTNAME',  (0,1),(-1,1), 'Helvetica-Bold')
    bt.setStyle(bts)
    story.append(bt)
    story.append(Spacer(1, 12))

    # Squad table
    story.append(Paragraph("Full Squad", section_s))
    squad_data = [["#", "Player", "Role", "Price Paid", "Impact", "Runs", "Wickets"]]
    role_colors = {"Batter": ACCENT, "Bowler": GREEN, "All-Rounder": PURPLE}
    for i, p in enumerate(req.players, 1):
        squad_data.append([str(i), p.player, p.role,
                           f"₹{p.price_paid}Cr", str(p.impact_score),
                           str(p.runs), str(p.wickets)])
    t = Table(squad_data, colWidths=[1*cm, 5*cm, 3*cm, 2.5*cm, 2*cm, 2*cm, 2*cm])
    ts = dark_table_style(ACCENT)
    for i, p in enumerate(req.players, 1):
        c = role_colors.get(p.role, TEXT)
        ts.add('TEXTCOLOR', (2, i), (2, i), c)
    t.setStyle(ts)
    story.append(t)

    story.append(Spacer(1, 20))
    story.append(Paragraph("Generated by IPL Intelligence Platform • For analyst use only",
                            ParagraphStyle('Footer', fontName='Helvetica', fontSize=7,
                                           textColor=MUTED, alignment=TA_CENTER)))
    doc.build(story)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/pdf",
                             headers={"Content-Disposition": "attachment; filename=ipl_squad_report.pdf"})


@router.post("/compare-pdf")
async def export_compare_pdf(req: CompareReportRequest):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    title_s, sub_s, section_s, body_s = make_styles()
    p1, p2 = req.player1, req.player2

    header_block(story, f"{p1.name}  vs  {p2.name}",
                 "Head-to-Head Player Comparison Report", title_s, sub_s)

    story.append(Paragraph("Impact Score Comparison", section_s))
    impact_data = [
        ["Metric", p1.name, p2.name, "Winner"],
        ["Impact Score", str(p1.impact_score), str(p2.impact_score),
         p1.name if p1.impact_score > p2.impact_score else p2.name],
        ["Batting Score", str(p1.batting_score), str(p2.batting_score),
         p1.name if p1.batting_score > p2.batting_score else p2.name],
        ["Bowling Score", str(p1.bowling_score), str(p2.bowling_score),
         p1.name if p1.bowling_score > p2.bowling_score else p2.name],
    ]
    it = Table(impact_data, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
    its = dark_table_style(PURPLE)
    its.add('TEXTCOLOR', (3,1), (3,-1), GREEN)
    its.add('FONTNAME',  (3,1), (3,-1), 'Helvetica-Bold')
    it.setStyle(its)
    story.append(it)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Detailed Stats Comparison", section_s))
    stats = [
        ["Stat", p1.name, p2.name, "Edge"],
        ["Runs", str(p1.runs), str(p2.runs),
         p1.name if p1.runs > p2.runs else p2.name],
        ["Strike Rate", str(p1.strike_rate), str(p2.strike_rate),
         p1.name if p1.strike_rate > p2.strike_rate else p2.name],
        ["Wickets", str(p1.wickets), str(p2.wickets),
         p1.name if p1.wickets > p2.wickets else p2.name],
        ["Economy", str(p1.economy), str(p2.economy),
         p1.name if p1.economy < p2.economy else p2.name],
    ]
    st = Table(stats, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
    sts = dark_table_style(ACCENT)
    sts.add('TEXTCOLOR', (3,1),(3,-1), GREEN)
    sts.add('FONTNAME',  (3,1),(3,-1), 'Helvetica-Bold')
    st.setStyle(sts)
    story.append(st)

    # Overall verdict
    story.append(Spacer(1, 16))
    winner = p1.name if p1.impact_score >= p2.impact_score else p2.name
    margin = abs(p1.impact_score - p2.impact_score)
    story.append(Paragraph("Verdict", section_s))
    story.append(Paragraph(
        f"<b>{winner}</b> has a higher overall impact score by <b>{margin:.2f} points</b>. "
        f"Based on career IPL data across batting, bowling and match contribution metrics.",
        body_s))

    story.append(Spacer(1, 20))
    story.append(Paragraph("Generated by IPL Intelligence Platform • For analyst use only",
                            ParagraphStyle('Footer', fontName='Helvetica', fontSize=7,
                                           textColor=MUTED, alignment=TA_CENTER)))
    doc.build(story)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/pdf",
                             headers={"Content-Disposition": "attachment; filename=player_comparison.pdf"})