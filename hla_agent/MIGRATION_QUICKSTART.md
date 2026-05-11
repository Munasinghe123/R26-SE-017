# 🚀 Quick Migration Guide

## Choose Your Migration Method

### ✅ Method 1: Preserve Commit History (RECOMMENDED for Research)
**Use this if:** You want to show development evolution in your research documentation

**Run:**
```bash
cd "e:\01 R\hla_agent"
migrate_to_new_repo.bat
```

**What it does:**
1. ✅ Backs up your current repository
2. ✅ Clones new repository
3. ✅ Preserves ALL commit history
4. ✅ Moves everything into `hla_agent/` folder
5. ✅ Pushes to GitHub

**Time:** ~5-10 minutes

---

### ⚡ Method 2: Fresh Start (SIMPLER)
**Use this if:** You just want to move the code quickly without history

**Run:**
```bash
cd "e:\01 R\hla_agent"
migrate_simple.bat
```

**What it does:**
1. ✅ Clones new repository
2. ✅ Copies all files to `hla_agent/` folder
3. ✅ Creates one comprehensive commit
4. ✅ Pushes to GitHub

**Time:** ~2-3 minutes

---

## 📋 Prerequisites

Before running either script:

1. **Install git-filter-repo** (Method 1 only):
```bash
pip install git-filter-repo
```

2. **Ensure Git is configured**:
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

3. **GitHub Authentication**:
   - Make sure you can push to https://github.com/Munasinghe123/R26-SE-017.git
   - Use Personal Access Token if needed

---

## 🎯 Recommended for Your Research

**Use Method 1 (Preserve History)** because:
- ✅ Shows iterative development (important for research integrity)
- ✅ Demonstrates evolution of features
- ✅ Provides audit trail for academic review
- ✅ Better for research documentation

---

## 🔧 After Migration

### 1. Verify Migration
```bash
cd "e:\01 R\R26-SE-017"
dir hla_agent
git log --oneline
```

### 2. Test Application
```bash
cd hla_agent
python main.py
```

### 3. Create Release Tag (Optional)
```bash
cd "e:\01 R\R26-SE-017"
git tag -a v1.0-research -m "Version submitted with research paper"
git push origin v1.0-research
```

### 4. Update Your Working Directory
From now on, work in:
```
e:\01 R\R26-SE-017\hla_agent\
```

---

## 📝 Create Repository README

After migration, create `README.md` in repository root:

```bash
cd "e:\01 R\R26-SE-017"
notepad README.md
```

**Content:**
```markdown
# R26-SE-017: Research Project Repository

## HLA Agent - Research-Grade Architecture Evaluation System

### Quick Start
See [hla_agent/docs/README_RESEARCH.md](hla_agent/docs/README_RESEARCH.md)

### Documentation
- [Research Methodology](hla_agent/docs/RESEARCH_METHODOLOGY.md)
- [Presentation Materials](hla_agent/docs/PRESENTATION_COMPLETE.md)
- [System Architecture](hla_agent/docs/SYSTEM_ARCHITECTURE.md)

### Research Contributions
- ATAM-inspired automated evaluation framework
- Style-specific validation for 5 canonical architecture patterns
- Deterministic, reproducible methodology
- Research-grade diagram evaluation with side-by-side diff

### Contact
[Your Name] - Research Unit SE-017
```

Then commit:
```bash
git add README.md
git commit -m "Add repository README"
git push origin main
```

---

## ⚠️ Troubleshooting

### Issue: "git-filter-repo not found"
```bash
pip install git-filter-repo
```

### Issue: "Permission denied (publickey)"
Set up GitHub authentication:
```bash
# Use HTTPS with Personal Access Token
git config --global credential.helper wincred
```

### Issue: "Merge conflicts"
Resolve manually:
```bash
git status
# Edit conflicted files
git add .
git commit -m "Resolve conflicts"
git push origin main
```

---

## 🆘 Need Help?

1. Check `docs/MIGRATION_GUIDE.md` for detailed instructions
2. Keep your backup safe: `e:\01 R\hla_agent_backup`
3. If migration fails, you can always start over

---

## ✅ Final Checklist

After migration:
- [ ] Code is in `R26-SE-017/hla_agent/` folder
- [ ] Pushed to GitHub successfully
- [ ] Application runs correctly
- [ ] README.md created in repository root
- [ ] Release tag created (optional)
- [ ] Paper references updated (if applicable)

**Your research code is now properly organized! 🎓**
